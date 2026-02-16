"""
Lambda handler for External Service (Team Gig 'Em).
Routes: POST /auth/signup, POST /auth/signin, POST /auth/forgot-password, POST /auth/reset-password,
        GET /me, PUT /me, POST /graduation-handover, GET /graduation-handover/history (admin),
        GET/POST /graduation-handover/claim, POST /graduation-handover/request-link,
        EventBridge graduation scan.
"""

import json
import os

import auth
import db
import role_engine
import handover
import handover_log
import graduation_scan
import graduation_claim

USER_POOL_ID = os.environ.get("USER_POOL_ID")
CLIENT_ID = os.environ.get("CLIENT_ID")
EXTERNAL_USERS_TABLE = os.environ.get("EXTERNAL_USERS_TABLE")
ADMIN_USER_IDS = set(x.strip() for x in os.environ.get("ADMIN_USER_IDS", "").split(",") if x.strip())


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
    path = (http.get("path") or event.get("rawPath") or event.get("path") or "/").strip("/")
    path_parts = [p for p in path.split("/") if p]
    body = _parse_body(event)
    return path_parts, method, body


# ---------------------------------------------------------------------------
# EventBridge: Graduation scan (Scheduled rule)
# ---------------------------------------------------------------------------
def do_graduation_scan() -> dict:
    """Scan students, generate tokens, deliver magic links."""
    try:
        result = graduation_scan.run_scan()
        return _response(result, 200)
    except Exception as e:
        return _response({"error": "Scan failed", "detail": str(e)}, 500)


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
    domain = email.split("@")[-1].lower()
    if domain != "tamu.edu":
        return _response({"error": "Registration requires a Texas A&M University email (@tamu.edu)"}, 400)
    if not password or len(password) < 10:
        return _response({"error": "Password must be at least 10 characters"}, 400)

    try:
        role, resolved_class_year = role_engine.resolve_role(email, former_student, class_year)
    except ValueError as e:
        return _response({"error": str(e)}, 400)

    try:
        signup_result = auth.sign_up(email, password)
        user_id = signup_result.get("UserSub")
        if not user_id:
            return _response({"error": "Registration failed", "detail": "No UserSub in Cognito response"}, 500)
    except auth.client.exceptions.UsernameExistsException:
        return _response({"error": "An account with this email already exists"}, 409)
    except Exception as e:
        return _response({"error": "Registration failed", "detail": str(e)}, 500)

    try:
        # Auto-confirm so user can sign in immediately (no email verification step)
        auth.admin_confirm_sign_up(email)

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
    except Exception as e:
        return _response({"error": "Registration failed", "detail": str(e)}, 500)

    return _response({
        "message": "Registration successful",
        "userId": user_id,
        "email": email,
        "role": role,
        "classYear": resolved_class_year,
    }, 201)


# ---------------------------------------------------------------------------
# POST /auth/forgot-password - send reset code to email
# Body: { "email" }
# ---------------------------------------------------------------------------
def do_forgot_password(body: dict) -> dict:
    email = (body.get("email") or "").strip().lower()
    if not email or "@" not in email:
        return _response({"error": "Valid email is required"}, 400)
    try:
        auth.forgot_password(email)
        return _response({"message": "If an account exists, a reset code was sent to your email."}, 200)
    except auth.client.exceptions.UserNotFoundException:
        return _response({"message": "If an account exists, a reset code was sent to your email."}, 200)
    except auth.client.exceptions.InvalidParameterException as e:
        return _response({"error": "Cannot reset password for this account", "detail": str(e)}, 400)
    except Exception as e:
        return _response({"error": "Request failed", "detail": str(e)}, 500)


# ---------------------------------------------------------------------------
# POST /auth/reset-password - set new password with code from email
# Body: { "email", "code", "newPassword" }
# ---------------------------------------------------------------------------
def do_reset_password(body: dict) -> dict:
    email = (body.get("email") or "").strip().lower()
    code = (body.get("code") or "").strip()
    new_password = body.get("newPassword") or ""
    if not email or "@" not in email:
        return _response({"error": "Valid email is required"}, 400)
    if not code:
        return _response({"error": "Reset code is required"}, 400)
    if not new_password or len(new_password) < 10:
        return _response({"error": "New password must be at least 10 characters"}, 400)
    try:
        auth.confirm_forgot_password(email, code, new_password)
        return _response({"message": "Password has been reset. You can sign in with your new password."}, 200)
    except auth.client.exceptions.CodeMismatchException:
        return _response({"error": "Invalid or expired code"}, 400)
    except auth.client.exceptions.ExpiredCodeException:
        return _response({"error": "Code has expired. Request a new one."}, 400)
    except Exception as e:
        return _response({"error": "Reset failed", "detail": str(e)}, 500)


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
    role = "FRIEND"
    class_year = None
    linked_uin = None
    for attr in cognito_user.get("UserAttributes", []):
        if attr["Name"] == "sub":
            sub = attr["Value"]
        elif attr["Name"] == "email":
            email = attr["Value"]
        elif attr["Name"] == "custom:role":
            role = attr["Value"]
        elif attr["Name"] == "custom:class_year":
            class_year = attr["Value"] or None
        elif attr["Name"] == "custom:linked_uin":
            linked_uin = attr["Value"] or None
    if not sub:
        return _response({"error": "User not found"}, 404)

    user_record = db.get_user_by_id(sub)
    if not user_record:
        # Lazy create: user has Cognito account but no DynamoDB record (e.g. from partial signup)
        if not email:
            return _response({"error": "Profile not found"}, 404)
        db.put_user(
            user_id=sub,
            email=email,
            role=role,
            class_year=class_year,
            linked_uin=linked_uin,
        )
        user_record = {"email": email, "role": role, "class_year": class_year, "linked_uin": linked_uin}

    return _response({
        "userId": sub,
        "email": user_record.get("email"),
        "role": user_record.get("role"),
        "classYear": user_record.get("class_year"),
        "linkedUin": user_record.get("linked_uin"),
        "linkedInUrl": user_record.get("linked_in_url"),
    })


# ---------------------------------------------------------------------------
# PUT /me - update profile (classYear, linkedInUrl)
# ---------------------------------------------------------------------------
def do_put_me(event: dict, body: dict) -> dict:
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
        elif attr["Name"] == "email":
            email = attr["Value"]
    if not sub:
        return _response({"error": "User not found"}, 404)

    class_year = (body.get("classYear") or "").strip() or None
    linked_in_url = (body.get("linkedInUrl") or "").strip() or None
    if "classYear" not in body and "linkedInUrl" not in body:
        return _response({"error": "Provide classYear and/or linkedInUrl to update"}, 400)

    user_record = db.get_user_by_id(sub) or {}
    try:
        db.update_profile(sub, class_year=class_year, linked_in_url=linked_in_url)
    except Exception as e:
        return _response({"error": "Update failed", "detail": str(e)}, 500)

    if class_year is not None and email:
        auth.admin_set_custom_attributes(
            username=email,
            role=user_record.get("role") or "FRIEND",
            class_year=class_year,
            linked_uin=user_record.get("linked_uin"),
        )

    user_record = db.get_user_by_id(sub) or {}
    return _response({
        "userId": sub,
        "email": user_record.get("email"),
        "role": user_record.get("role"),
        "classYear": user_record.get("class_year"),
        "linkedUin": user_record.get("linked_uin"),
        "linkedInUrl": user_record.get("linked_in_url"),
    })


# ---------------------------------------------------------------------------
# POST /graduation-handover
# Body: { "uin", "classYear": optional, "personalEmail", "password" }
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
    email = None
    for attr in cognito_user.get("UserAttributes", []):
        if attr["Name"] == "sub":
            sub = attr["Value"]
        elif attr["Name"] == "email":
            email = attr["Value"]
    if not sub:
        return _response({"error": "User not found"}, 404)

    user_record = db.get_user_by_id(sub)
    if user_record and user_record.get("role") == "FORMER_STUDENT":
        return _response({"error": "Already linked to a student UIN"}, 403)

    uin = (body.get("uin") or "").strip()
    class_year = (body.get("classYear") or "").strip() or None
    personal_email = (body.get("personalEmail") or "").strip().lower()
    password = body.get("password")

    if not personal_email or "@" not in personal_email:
        return _response({"error": "Personal email is required"}, 400)
    if not password:
        return _response({"error": "Password is required to verify your identity"}, 400)
    if not email or "@" not in email:
        return _response({"error": "Could not determine account email"}, 500)

    # Verify password (user's TAMU/account password)
    try:
        auth.initiate_auth(email, password)
    except auth.client.exceptions.NotAuthorizedException:
        return _response({"error": "Invalid password"}, 401)
    except auth.client.exceptions.UserNotFoundException:
        return _response({"error": "Invalid password"}, 401)
    except Exception as e:
        return _response({"error": "Password verification failed", "detail": str(e)}, 500)

    personal_email_clean = (body.get("personalEmail") or "").strip().lower()
    handover_id = handover_log.log_initiated(sub, uin, personal_email_clean or "")

    try:
        result = handover.link_uin_to_user(sub, uin, class_year, personal_email=personal_email)
    except Exception as e:
        handover_log.log_failed(handover_id, sub, uin, reason=str(e))
        return _response({"error": "Handover failed", "detail": str(e)}, 500)

    if "error" in result:
        handover_log.log_failed(handover_id, sub, uin, reason=result.get("error"))
        return _response({"error": result["error"]}, result.get("status", 400))
    handover_log.log_success(handover_id, sub, uin)
    return _response(result)


# ---------------------------------------------------------------------------
# GET /graduation-handover/history - admin only (ADMIN_USER_IDS)
# ---------------------------------------------------------------------------
def do_handover_history(event: dict) -> dict:
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
    if not sub or sub not in ADMIN_USER_IDS:
        return _response({"error": "Forbidden"}, 403)

    entries = handover_log.list_recent(limit=100)
    return _response({"entries": entries})


def lambda_handler(event: dict, context: object) -> dict:
    # EventBridge scheduled invocation (graduation scan)
    if event.get("source") == "aws.events" or event.get("detail-type") == "Scheduled Event":
        return do_graduation_scan()

    path_parts, method, body = _route(event)

    # CORS preflight - return 200 for all OPTIONS requests
    if method == "OPTIONS":
        return _response({}, 200)

    # Health / root
    if not path_parts and method == "GET":
        return _response({"service": "external", "version": "1.0"})

    # POST /auth/signup
    if path_parts == ["auth", "signup"] and method == "POST":
        return do_signup(body)

    # POST /auth/forgot-password
    if path_parts == ["auth", "forgot-password"] and method == "POST":
        return do_forgot_password(body)

    # POST /auth/reset-password
    if path_parts == ["auth", "reset-password"] and method == "POST":
        return do_reset_password(body)

    # POST /auth/signin
    if path_parts == ["auth", "signin"] and method == "POST":
        return do_signin(body)

    # GET /me
    if path_parts == ["me"] and method == "GET":
        return do_me(event)

    # PUT /me
    if path_parts == ["me"] and method == "PUT":
        return do_put_me(event, body)

    # GET /graduation-handover/history (admin)
    if path_parts == ["graduation-handover", "history"] and method == "GET":
        return do_handover_history(event)

    # POST /graduation-handover
    if path_parts == ["graduation-handover"] and method == "POST":
        return do_graduation_handover(event, body)

    # POST /graduation-handover/request-link - self-service: request magic link by email
    if path_parts == ["graduation-handover", "request-link"] and method == "POST":
        email = (body.get("email") or "").strip().lower()
        result = graduation_scan.request_magic_link_for_email(email)
        if "error" in result:
            return _response({"error": result["error"]}, result.get("status", 400))
        return _response(result, 200)

    # GET /graduation-handover/claim?token=xxx - validate token, return email/uin for UI
    if path_parts == ["graduation-handover", "claim"] and method == "GET":
        query = event.get("queryStringParameters") or {}
        token = query.get("token", "").strip()
        info = graduation_claim.get_token_info(token)
        if not info:
            return _response({"error": "Invalid or expired token"}, 400)
        return _response({"email": info["personal_email"], "uin": info["uin"], "classYear": info["class_year"]})

    # POST /graduation-handover/claim - complete claim with password
    if path_parts == ["graduation-handover", "claim"] and method == "POST":
        token = (body.get("token") or "").strip()
        password = body.get("password") or ""
        result = graduation_claim.claim_with_password(token, password)
        if "error" in result:
            return _response({"error": result["error"]}, result.get("status", 400))
        return _response(result, 200)

    return _response({"error": "Not Found", "path": "/" + "/".join(path_parts)}, 404)
