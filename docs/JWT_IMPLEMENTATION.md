# JWT Authentication with Refresh Tokens

This document describes the secure JWT authentication implementation with refresh token rotation.

## Overview

The new JWT implementation includes:

- **Access Tokens**: Short-lived tokens (default: 30 minutes) for API access
- **Refresh Tokens**: Long-lived tokens (default: 7 days) stored in database
- **Token Rotation**: Each refresh generates new tokens and invalidates old ones
- **Token Revocation**: Ability to revoke specific tokens or all user tokens
- **Security Tracking**: IP address and user agent tracking for audit purposes

## Database Schema

### RefreshToken Model

```sql
CREATE TABLE refresh_tokens (
    id SERIAL PRIMARY KEY,
    token_id VARCHAR UNIQUE NOT NULL,  -- JWT ID (jti claim)
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR NOT NULL,       -- Hashed version of the token
    expires_at TIMESTAMP NOT NULL,
    is_revoked BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    used_at TIMESTAMP,                 -- When the token was last used
    ip_address VARCHAR,                -- IP address when token was created
    user_agent VARCHAR                 -- User agent when token was created
);
```

## API Endpoints

### Authentication Flow

1. **Login** (`POST /api/v1/auth/login`)
   - Accepts username/password via OAuth2 form
   - Returns access token and refresh token
   - Stores refresh token in database with client info

2. **Refresh** (`POST /api/v1/auth/refresh`)
   - Accepts refresh token
   - Validates token against database
   - Returns new access token and new refresh token
   - Marks old refresh token as used (rotation)

3. **Logout** (`POST /api/v1/auth/logout`)
   - Accepts refresh token
   - Revokes the specific token

4. **Logout All** (`POST /api/v1/auth/logout-all`)
   - Requires valid access token
   - Revokes all refresh tokens for the user

5. **Get Current User** (`GET /api/v1/auth/me`)
   - Requires valid access token
   - Returns current user information

## Security Features

### Token Structure

**Access Token Claims:**
```json
{
  "sub": "user_id",
  "email": "user@example.com",
  "exp": "expiration_timestamp",
  "iat": "issued_at_timestamp",
  "type": "access"
}
```

**Refresh Token Claims:**
```json
{
  "sub": "user_id",
  "email": "user@example.com",
  "exp": "expiration_timestamp",
  "iat": "issued_at_timestamp",
  "jti": "unique_token_id",
  "type": "refresh"
}
```

### Security Measures

1. **Token Rotation**: Each refresh generates new tokens
2. **Database Storage**: Refresh tokens stored with hashes
3. **Revocation**: Tokens can be individually revoked
4. **Rate Limiting**: Refresh endpoint limited to 10/minute
5. **Audit Trail**: IP address and user agent tracking
6. **Cascade Deletion**: Tokens deleted when user is deleted

## Usage Examples

### Frontend Implementation

```javascript
// Login
const login = async (email, password) => {
  const formData = new FormData();
  formData.append('username', email);
  formData.append('password', password);
  
  const response = await fetch('/api/v1/auth/login', {
    method: 'POST',
    body: formData
  });
  
  const data = await response.json();
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);
};

// Refresh token
const refreshToken = async () => {
  const refresh_token = localStorage.getItem('refresh_token');
  
  const response = await fetch('/api/v1/auth/refresh', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ refresh_token })
  });
  
  const data = await response.json();
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);
};

// Logout
const logout = async () => {
  const refresh_token = localStorage.getItem('refresh_token');
  
  await fetch('/api/v1/auth/logout', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ refresh_token })
  });
  
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
};
```

### Backend Usage

```python
from app.services import auth_service

# Create tokens
access_token = auth_service.create_access_token(
    data={"sub": str(user.id), "email": user.email}
)
refresh_token = auth_service.create_refresh_token(
    data={"sub": str(user.id), "email": user.email},
    db=db,
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent")
)

# Validate tokens
user_id = auth_service.decode_access_token(token)
result = auth_service.decode_refresh_token(refresh_token, db)

# Revoke tokens
auth_service.revoke_refresh_token(refresh_token, db)
auth_service.revoke_all_user_refresh_tokens(user_id, db)
```

## Configuration

### Environment Variables

```env
JWT_SECRET=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30
JWT_REFRESH_EXPIRATION_DAYS=7
```

### Rate Limiting

- Login: 5 attempts per hour
- Refresh: 10 attempts per minute

## Maintenance

### Database Cleanup

Run the cleanup script periodically to remove expired tokens:

```bash
python -m app.utils.token_cleanup
```

### Migration

To add the refresh_tokens table to existing databases:

```bash
python -m app.db.migrations.add_refresh_tokens_table
```

## Security Best Practices

1. **Store refresh tokens securely**: Use HttpOnly cookies in production
2. **Implement token refresh**: Automatically refresh tokens before expiration
3. **Monitor token usage**: Log suspicious activity
4. **Regular cleanup**: Remove expired tokens from database
5. **Password changes**: Revoke all tokens when password changes
6. **HTTPS only**: Always use HTTPS in production

## Troubleshooting

### Common Issues

1. **Token not found**: Check if token exists in database
2. **Token expired**: Check expiration time
3. **Token revoked**: Check is_revoked flag
4. **Rate limit exceeded**: Wait before retrying

### Debugging

Enable debug logging to see token operations:

```python
import logging
logging.getLogger('app.services.auth_service').setLevel(logging.DEBUG)
```

## Migration from Old Implementation

If migrating from the old JWT implementation:

1. Run the database migration
2. Update frontend to handle token rotation
3. Implement proper error handling for revoked tokens
4. Update any hardcoded token validation logic 

User Login:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Frontend  │    │   Backend   │    │  Database   │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       │ POST /login       │                   │
       │───────────────────│                   │
       │                   │                   │
       │                   │ Create Access Token│
       │                   │ (2 min expiry)    │
       │                   │                   │
       │                   │ Create Refresh Token│
       │                   │ (7 day expiry)    │
       │                   │                   │
       │                   │ Store in DB       │
       │                   │───────────────────│
       │                   │                   │
       │ Return both tokens│                   │
       │◄──────────────────│                   │
       │                   │                   │

Normal API Request:
       │                   │                   │
       │ GET /api/me       │                   │
       │ + Access Token    │                   │
       │───────────────────│                   │
       │                   │ Validate Token    │
       │                   │ (no DB check)     │
       │                   │                   │
       │ Return User Data  │                   │
       │◄──────────────────│                   │

Token Expired:
       │                   │                   │
       │ GET /api/me       │                   │
       │ + Expired Token   │                   │
       │───────────────────│                   │
       │                   │ Return 401        │
       │◄──────────────────│                   │
       │                   │                   │
       │ POST /refresh     │                   │
       │ + Refresh Token   │                   │
       │───────────────────│                   │
       │                   │ Check DB          │
       │                   │───────────────────│
       │                   │                   │
       │                   │ Create New Tokens │
       │                   │                   │
       │ Return New Tokens │                   │
       │◄──────────────────│                   │