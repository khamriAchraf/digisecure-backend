from passlib.context import CryptContext

from app.core.logger import logger, request_id_ctx
from app.db.models.group import Group
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


def access_filters(user: User, resource_model):
    """
    Build SQLAlchemy filters for querying resources based on user access rules.

    This function creates filters that mimic the rules in the can_access function:
    1. Direct assignment (resource.assigned_to == user.id)
    2. Group membership (shared groups between user and resource)
    3. Many-to-many group membership (resource.groups relationship)
    4. Super Admin override (if user is Super-Admin, no filters applied)

    Args:
        user: User object with id, groups, and role attributes
        resource_model: SQLAlchemy model class (e.g., Asset) to build filters for

    Returns:
        list: List of SQLAlchemy filter expressions, or None if no filters needed (Super-Admin)
    """
    from sqlalchemy import or_

    # Super Admin override - no filters needed
    if user.role and user.role.name == "Super-Admin":
        return None

    # Get user's group IDs (direct membership)
    user_group_ids = {group.id for group in user.groups}

    # Only direct group memberships (no hierarchical access)
    accessible_group_ids = set(user_group_ids)

    # Build filter conditions
    conditions = []

    # 1. Direct assignment
    if hasattr(resource_model, "assigned_to"):
        conditions.append(resource_model.assigned_to == user.id)

    # 2. Group membership via foreign key (exact same group only)
    if hasattr(resource_model, "group_id") and accessible_group_ids:
        conditions.append(resource_model.group_id.in_(accessible_group_ids))

    # 3. Many-to-many group membership (exact same group only)
    if hasattr(resource_model, "groups") and accessible_group_ids:
        from app.db.models.group import Group  # local import to avoid circular

        conditions.append(resource_model.groups.any(Group.id.in_(accessible_group_ids)))

    # If no conditions were built, return empty list (no access)
    if not conditions:
        return []

    # Return OR condition for all access methods
    return [or_(*conditions)]


def can_access(user: User, resource) -> bool:
    """
    Determine whether a user has the right to view or interact with a specific resource instance.

    This function checks access based on:
    1. Direct assignment (resource.assigned_to == user.id)
    2. Group membership (shared groups between user and resource)
    3. Group access (for Group resources - user must be member and have update permissions)

    Args:
        user: User object with id, groups, and location attributes
        resource: Resource instance (e.g., Asset, Group) with assigned_to, group_id, location_id attributes

    Returns:
        bool: True if access is allowed, False otherwise
    """
    outcome = False
    access_reason = "none"

    if isinstance(resource, Group):
        user_group_ids = {group.id for group in user.groups}
        if resource.id in user_group_ids and has_permission(user, "update", "group"):
            outcome = True
            access_reason = "group_member_with_update_permission"
        else:
            outcome = False
            access_reason = "not_group_member_or_no_update_permission"
    elif isinstance(resource, User):
        # Users cannot access (read/update/delete/purge) a user with a higher-privilege role
        # Lower rank value means higher privilege
        requester_rank = user.role.rank if getattr(user, "role", None) else float("inf")
        target_rank = (
            resource.role.rank if getattr(resource, "role", None) else float("inf")
        )

        if requester_rank > target_rank:
            outcome = False
            access_reason = "target_user_has_higher_rank"
        else:
            outcome = True
            access_reason = "user_rank_check_allowed"
    else:
        # 1. Direct Assignment Check
        if hasattr(resource, "assigned_to") and resource.assigned_to == user.id:
            outcome = True
            access_reason = "direct_assignment"

        # 2. Group Membership Check (many-to-many via groups; exact same group only)
        elif hasattr(resource, "groups") and resource.groups:
            user_group_ids = {group.id for group in user.groups}
            resource_group_ids = {group.id for group in resource.groups}
            if user_group_ids.intersection(resource_group_ids):
                outcome = True
                access_reason = "group_membership_m2m"

    # 4. Super Admin Override
    if user.role and user.role.name == "Super-Admin":
        outcome = True
        access_reason = "super_admin"

    log_method = logger.info if outcome else logger.warning
    log_method(
        "access_check",
        extra={
            "log_type": "access",
            "request_id": request_id_ctx.get() or "-",
            "user_id": getattr(user, "id", None),
            "resource_type": type(resource).__name__,
            "resource_id": getattr(resource, "id", None),
            "access_reason": access_reason,
            "success": outcome,
        },
    )

    return outcome


def authorize(user: User, action: str, resource: str, resource_instance=None) -> bool:
    """
    Combined authorization check that validates both role-based permission and
    optional instance-level access.

    Rules:
    - Super-Admin: always authorized
    - If no resource_instance is provided: only role permission is required
    - If resource_instance is provided: requires role permission AND can_access
    """
    # Super Admin override
    if user.role and user.role.name == "Super-Admin":
        logger.info(
            "authorization_check",
            extra={
                "log_type": "authorization",
                "request_id": request_id_ctx.get() or "-",
                "user_id": getattr(user, "id", None),
                "action": action,
                "resource": resource,
                "resource_type": (
                    type(resource_instance).__name__ if resource_instance else None
                ),
                "resource_id": (
                    getattr(resource_instance, "id", None)
                    if resource_instance
                    else None
                ),
                "access_reason": "super_admin",
                "success": True,
            },
        )
        return True

    has_perm = has_permission(user, action, resource)
    if not has_perm:
        logger.warning(
            "authorization_check",
            extra={
                "log_type": "authorization",
                "request_id": request_id_ctx.get() or "-",
                "user_id": getattr(user, "id", None),
                "action": action,
                "resource": resource,
                "resource_type": (
                    type(resource_instance).__name__ if resource_instance else None
                ),
                "resource_id": (
                    getattr(resource_instance, "id", None)
                    if resource_instance
                    else None
                ),
                "access_reason": "no_permission",
                "success": False,
            },
        )
        return False

    # Allow listing users regardless of rank (permission-only)
    if resource == "user" and action == "list":
        logger.info(
            "authorization_check",
            extra={
                "log_type": "authorization",
                "request_id": request_id_ctx.get() or "-",
                "user_id": getattr(user, "id", None),
                "action": action,
                "resource": resource,
                "resource_type": None,
                "resource_id": None,
                "access_reason": "list_no_rank_restriction",
                "success": True,
            },
        )
        return True

    if resource_instance is None:
        logger.info(
            "authorization_check",
            extra={
                "log_type": "authorization",
                "request_id": request_id_ctx.get() or "-",
                "user_id": getattr(user, "id", None),
                "action": action,
                "resource": resource,
                "resource_type": None,
                "resource_id": None,
                "access_reason": "permission_only",
                "success": True,
            },
        )
        return True

    has_access = can_access(user, resource_instance)
    log_method = logger.info if has_access else logger.warning
    log_method(
        "authorization_check",
        extra={
            "log_type": "authorization",
            "request_id": request_id_ctx.get() or "-",
            "user_id": getattr(user, "id", None),
            "action": action,
            "resource": resource,
            "resource_type": type(resource_instance).__name__,
            "resource_id": getattr(resource_instance, "id", None),
            "access_reason": (
                "permission_and_access" if has_access else "no_resource_access"
            ),
            "success": has_access,
        },
    )
    return has_access
