"""
Lambda handler for External Service (Team Gig 'Em).
Routes: POST /auth/signup, POST /auth/signin, GET /me, POST /graduation-handover
"""

import json
import os

import auth
import db
import role_engine
import handover

USER_POOL_ID = os.environ.get("USER_POOL_ID")
CLIENT_ID = os.environ.get("CLIENT_ID")
EXTERNAL_USERS_TABLE = os.environ.get("EXTERNAL_USERS_TABLE")


def _response(body: dict, status: int = 200, cors: bool = True) -> dict:
    h = {"Content-Type": "application/json"}
    if cors:
        h["Access-Control-Allow-Origin"] = "*"
        h["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return {"statusCode": status, "headers": h, "body": json.dumps(body)}


def _parse_body(event: dict) -> dict:
    raw = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        import base64
        raw = base64.b64decode(raw).decode("utf-8")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def _route(event: dict) -> tuple:
    """Return (path_parts, method, body)."""
    req = event.get("requestContext", {}) or {}
    http = req.get("http", {})
    method = (http.get("method") or event.get("httpMethod") or "GET").upper()
    path = (http.get("path") or event.get("path") or "/").strip("/")
    path_parts = [p for p in path.split("/") if p]
    body = _parse_body(event)
    return path_parts, method, body


# ---------------------------------------------------------------------------
# POST /auth/signup
# Body: { "email", "password", "formerStudent": bool, "classYear": optional }
# ---------------------------------------------------------------------------
def do_signup(body: dict) -> dict:
    email = (body.get("email") or "").strip().lower()
    password = body.get("password")
    former_student = body.get("formerStudent", False)
    class_year = (body.get("classYear") or "").strip() or None

    if not email or "@" not in email:
        return _response({"error": "Valid email is required"}, 400)
    if not password or len(password) < 10:
        return _response({"error": "Password must be at least 10 characters"}, 400)

    try:
        role, resolved_class_year = role_engine.resolve_role(email, former_student, class_year)
    except ValueError as e:
        return _response({"error": str(e)}, 400)

    try:
        auth.sign_up(email, password)
    except auth.client.exceptions.UsernameExistsException:
        return _response({"error": "An account with this email already exists"}, 409)
    except Exception as e:
        return _response({"error": "Registration failed", "detail": str(e)}, 500)

    # Auto-confirm so user can sign in immediately (no email verification step)
    auth.admin_confirm_sign_up(email)

    # Get sub from Cognito (list_users by email)
    import boto3
    cognito = boto3.client("cognito-idp")
    r = cognito.list_users(UserPoolId=USER_POOL_ID, Filter=f'email = "{email}"', Limit=1)
    users = r.get("Users", [])
    if not users:
        return _response({"error": "User created but could not retrieve user id"}, 500)
    user_id = users[0]["Username"]

    auth.admin_set_custom_attributes(
        username=email,
        role=role,
        class_year=resolved_class_year,
        linked_uin=None,
    )
    db.put_user(
        user_id=user_id,
        email=email,
        role=role,
        class_year=resolved_class_year,
        linked_uin=None,
    )

    return _response({
        "message": "Registration successful",
        "userId": user_id,
        "email": email,
        "role": role,
        "classYear": resolved_class_year,
    }, 201)


# ---------------------------------------------------------------------------
# POST /auth/signin
# Body: { "email", "password" }
# ---------------------------------------------------------------------------
def do_signin(body: dict) -> dict:
    email = (body.get("email") or "").strip().lower()
    password = body.get("password")

    if not email or not password:
        return _response({"error": "Email and password are required"}, 400)

    try:
        result = auth.initiate_auth(email, password)
    except auth.client.exceptions.NotAuthorizedException:
        return _response({"error": "Invalid email or password"}, 401)
    except auth.client.exceptions.UserNotFoundException:
        return _response({"error": "Invalid email or password"}, 401)
    except Exception as e:
        return _response({"error": "Sign in failed", "detail": str(e)}, 500)

    auth_result = result.get("AuthenticationResult", {})
    id_token = auth_result.get("IdToken")
    access_token = auth_result.get("AccessToken")
    refresh_token = auth_result.get("RefreshToken")
    expires_in = auth_result.get("ExpiresIn")

    user_record = db.get_user_by_email(email)
    role = (user_record or {}).get("role", "FRIEND")
    class_year = (user_record or {}).get("class_year")
    linked_uin = (user_record or {}).get("linked_uin")

    return _response({
        "idToken": id_token,
        "accessToken": access_token,
        "refreshToken": refresh_token,
        "expiresIn": expires_in,
        "user": {
            "email": email,
            "role": role,
            "classYear": class_year,
            "linkedUin": linked_uin,
        },
    })


# ---------------------------------------------------------------------------
# GET /me - current user from Bearer token
# ---------------------------------------------------------------------------
def do_me(event: dict) -> dict:
    token = auth.parse_token_from_header(event.get("headers") or {})
    if not token:
        return _response({"error": "Authorization required"}, 401)
    try:
        cognito_user = auth.get_user_by_token(token)
    except Exception:
        return _response({"error": "Invalid or expired token"}, 401)

    sub = None
    email = None
    for attr in cognito_user.get("UserAttributes", []):
        if attr["Name"] == "sub":
            sub = attr["Value"]
        if attr["Name"] == "email":
            email = attr["Value"]
    if not sub:
        return _response({"error": "User not found"}, 404)

    user_record = db.get_user_by_id(sub)
    if not user_record:
        return _response({"error": "Profile not found"}, 404)

    return _response({
        "userId": sub,
        "email": user_record.get("email"),
        "role": user_record.get("role"),
        "classYear": user_record.get("class_year"),
        "linkedUin": user_record.get("linked_uin"),
    })


# ---------------------------------------------------------------------------
# POST /graduation-handover
# Body: { "uin", "classYear": optional }
# ---------------------------------------------------------------------------
def do_graduation_handover(event: dict, body: dict) -> dict:
    token = auth.parse_token_from_header(event.get("headers") or {})
    if not token:
        return _response({"error": "Authorization required"}, 401)
    try:
        cognito_user = auth.get_user_by_token(token)
    except Exception:
        return _response({"error": "Invalid or expired token"}, 401)

    sub = None
    for attr in cognito_user.get("UserAttributes", []):
        if attr["Name"] == "sub":
            sub = attr["Value"]
            break
    if not sub:
        return _response({"error": "User not found"}, 404)

    uin = (body.get("uin") or "").strip()
    class_year = (body.get("classYear") or "").strip() or None

    result = handover.link_uin_to_user(sub, uin, class_year)
    if "error" in result:
        return _response({"error": result["error"]}, result.get("status", 400))
    return _response(result)


def lambda_handler(event: dict, context: object) -> dict:
    path_parts, method, body = _route(event)

    # Health / root
    if not path_parts and method == "GET":
        return _response({"service": "external", "version": "1.0"})

    # POST /auth/signup
    if path_parts == ["auth", "signup"] and method == "POST":
        return do_signup(body)

    # POST /auth/signin
    if path_parts == ["auth", "signin"] and method == "POST":
        return do_signin(body)

    # GET /me
    if path_parts == ["me"] and method == "GET":
        return do_me(event)

    # POST /graduation-handover
    if path_parts == ["graduation-handover"] and method == "POST":
        return do_graduation_handover(event, body)

    return _response({"error": "Not Found", "path": "/" + "/".join(path_parts)}, 404)
