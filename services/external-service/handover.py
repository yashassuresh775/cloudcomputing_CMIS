"""
Graduation Handover: link a new external account to an old Student UIN,
transferring history and setting primary role to FORMER_STUDENT.
"""

from typing import Optional

import db
import auth


def link_uin_to_user(user_id: str, uin: str, class_year: Optional[str] = None) -> dict:
    """
    Link external user to student UIN (graduation handover).
    - Validates user exists and UIN not already linked to another account.
    - Updates DynamoDB: role=FORMER_STUDENT, linked_uin=uin.
    - Updates Cognito custom attributes.
    Returns updated user info.
    """
    existing = db.get_user_by_id(user_id)
    if not existing:
        return {"error": "User not found", "status": 404}

    if existing.get("linked_uin"):
        return {"error": "Account already linked to a student UIN", "status": 409}

    other = db.get_user_by_linked_uin(uin)
    if other and other.get("user_id") != user_id:
        return {"error": "This UIN is already linked to another account", "status": 409}

    uin_clean = str(uin).strip()
    if not uin_clean:
        return {"error": "UIN is required", "status": 400}

    db.update_user_role_and_uin(user_id, "FORMER_STUDENT", uin_clean)
    if class_year:
        db.table.update_item(
            Key={"user_id": user_id},
            UpdateExpression="SET class_year = :y",
            ExpressionAttributeValues={":y": str(class_year).strip()},
        )

    # Update Cognito custom attributes so tokens reflect new role and UIN
    email = existing.get("email")
    if email:
        auth.admin_set_custom_attributes(
            username=email,
            role="FORMER_STUDENT",
            class_year=class_year or existing.get("class_year"),
            linked_uin=uin_clean,
        )

    updated = db.get_user_by_id(user_id)
    return {"user": updated, "message": "Graduation handover complete"}
