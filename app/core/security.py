from passlib.context import CryptContext

from app.db.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def has_permission(user: User, action: str, resource: str) -> bool:
    for role in user.roles:
        for perm in role.permissions:
            if perm.action == action and perm.resource == resource:
                return True
    return False
