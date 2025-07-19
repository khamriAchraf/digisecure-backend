from passlib.context import CryptContext

from app.core.logger import logger, request_id_ctx
from app.db.models.user import User

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__memory_cost=65536,
    argon2__time_cost=4,
    argon2__parallelism=2,
)


def get_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def has_permission(user: User, action: str, resource: str) -> bool:
    outcome = False
    if user.role:
        for perm in user.role.permissions:
            if perm.action == action and perm.resource == resource:
                outcome = True
                break
    log_method = logger.info if outcome else logger.warning
    log_method(
        "permission_check",
        extra={
            "log_type": "permission",
            "request_id": request_id_ctx.get() or "-",
            "user_id": getattr(user, "id", None),
            "action": action,
            "resource": resource,
            "success": outcome,
        },
    )
    return outcome


def has_permission_from_token(token_payload: dict, action: str, resource: str) -> bool:
    """Check permission from token payload data (more efficient than database query)"""
    outcome = False
    permissions = token_payload.get("permissions", [])
    required_permission = f"{resource}:{action}"

    if required_permission in permissions:
        outcome = True

    log_method = logger.info if outcome else logger.warning
    log_method(
        "permission_check_from_token",
        extra={
            "log_type": "permission",
            "request_id": request_id_ctx.get() or "-",
            "user_id": token_payload.get("sub"),
            "action": action,
            "resource": resource,
            "success": outcome,
        },
    )
    return outcome
