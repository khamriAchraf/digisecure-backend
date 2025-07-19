# JWT Token Structure with Role and Permissions

## Overview

The JWT tokens now include role information and permissions to enable more efficient permission checking without requiring database queries for every permission check.

## Token Structure

### Access Token Payload

```json
{
  "sub": "123",
  "email": "user@example.com",
  "role_id": 1,
  "permissions": ["user:read", "user:create", "role:read"],
  "exp": 1640995200,
  "iat": 1640991600,
  "type": "access"
}
```

### Refresh Token Payload

```json
{
  "sub": "123",
  "email": "user@example.com",
  "role_id": 1,
  "permissions": ["user:read", "user:create", "role:read"],
  "exp": 1643587200,
  "iat": 1640991600,
  "jti": "",
  "type": "refresh"
}
```

## Permission Format

Permissions are stored in the format `"resource:action"` where:
- `resource` is the entity being accessed (e.g., "user", "role", "asset")
- `action` is the operation being performed (e.g., "read", "create", "update", "delete")

### Examples
- `"user:read"` - Permission to read user data
- `"user:create"` - Permission to create new users
- `"role:update"` - Permission to update roles
- `"asset:delete"` - Permission to delete assets

## Usage

### Creating Tokens

Tokens are automatically created with role and permission information during login and token refresh:

```python
# Token data is automatically prepared in auth endpoints
token_data = {
    "sub": str(user.id), 
    "email": user.email,
    "role_id": user.role.id if user.role else None,
    "permissions": auth_service._get_user_permissions(user)
}

access_token = auth_service.create_access_token(data=token_data)
refresh_token = auth_service.create_refresh_token(data=token_data, db=db)
```

### Permission Checking

You can check permissions using the token payload for better performance:

```python
from app.core.security import has_permission_from_token
from app.services.auth_service import decode_access_token_payload

# Decode token to get payload
token_payload = decode_access_token_payload(token)
if token_payload:
    # Check permission from token (no database query needed)
    has_permission = has_permission_from_token(token_payload, "read", "user")
```

### Backward Compatibility

The existing `has_permission(user, action, resource)` function still works and will query the database if needed. The new token-based permission checking is an optimization that can be used when you already have the token payload.

## Benefits

1. **Performance**: Permission checks can be done without database queries
2. **Reduced Load**: Less database traffic for permission validation
3. **Caching**: Permissions are cached in the token for the token's lifetime
4. **Scalability**: Better performance under high load

## Security Considerations

- Permissions in tokens are only valid for the token's lifetime
- If user permissions change, they need to re-authenticate to get updated tokens
- Token refresh will include updated permissions if the user's role has changed
- The `role_id` can be used to quickly identify the user's role without additional queries

## Migration

This change is backward compatible. Existing code using `has_permission(user, action, resource)` will continue to work. The new token-based permission checking is an optional optimization. 