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
    for role in user.roles:
        for perm in role.permissions:
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
