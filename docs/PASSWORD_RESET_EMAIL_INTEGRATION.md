# Email Integration with Java Cron Job Service

This document describes the integration between the FastAPI backend and the Java cron job service for sending emails (password reset and welcome emails).

## Overview

The application uses an external Java-based email service built on Quartz Scheduler for all email communications. This service handles email delivery asynchronously and supports callback URLs for job result notifications.

### Email Types

1. **Password Reset Emails**: Sent when a user requests to reset their password
2. **Welcome Emails**: Sent when a new user account is created (includes credentials)

## Architecture

```
┌─────────────┐      ┌──────────────────┐      ┌─────────────────────┐
│   Client    │──1──▶│  FastAPI Backend │──2──▶│ Java Email Service  │
│ (Frontend)  │      │  /auth/forgot-   │      │  (Quartz Scheduler) │
└─────────────┘      │   password       │      └─────────────────────┘
                     └──────────────────┘               │
                              ▲                         │
                              │                         ▼
                              │                   ┌──────────┐
                              └─────────3─────────│  SMTP    │
                                                  │ Server   │
                                                  └──────────┘
```

1. User requests password reset
2. Backend creates token and calls Java email service
3. Java service schedules and sends email via SMTP

## Configuration

### Environment Variables

Add the following to your `.env` file:

```bash
# Email Service Configuration
EMAIL_SERVICE_URL=http://localhost:8080
PASSWORD_RESET_URL=http://localhost:3000/reset-password

# Password Reset Token Settings
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES=30
```

### Configuration Details

| Variable | Description | Default |
|----------|-------------|---------|
| `EMAIL_SERVICE_URL` | Base URL of the Java email service | `http://localhost:8080` |
| `PASSWORD_RESET_URL` | Frontend URL for password reset page | `http://localhost:3000/reset-password` |
| `PASSWORD_RESET_TOKEN_EXPIRE_MINUTES` | Token expiration time in minutes | `30` |

## Java Email Service API

### Endpoint: `POST /api/v1/send-email`

**Request Body:**
```json
{
  "to": ["user@example.com"],
  "subject": "Password Reset Request",
  "body": "Your password reset email content...",
  "requestId": "optional-tracking-id",
  "callbackUrl": "optional-callback-url"
}
```

**Response:**
- `200/201/202`: Email scheduled successfully
- `4xx/5xx`: Error scheduling email

**Example with cURL:**
```bash
curl -X POST http://localhost:8080/api/v1/send-email \
  -H "Content-Type: application/json" \
  -d '{
    "to": ["user@example.com"],
    "subject": "Password Reset Request",
    "body": "Click here to reset: http://localhost:3000/reset-password?token=abc123"
  }'
```

## Backend Implementation

### Email Service Module

Location: `app/services/email_service.py`

Key functions:
- `send_email_async()`: Async function to send emails via HTTP to the Java service
- `send_password_reset_email()`: Sends password reset emails (in French)
- `send_welcome_email()`: Sends welcome emails with credentials to new users (in French)
- `_run_async_email()`: Helper to run async email sending from sync contexts

### Usage in Auth Endpoint

The `/auth/forgot-password` endpoint:

1. Validates the email address
2. Creates a password reset token
3. Calls `send_password_reset_email()` with:
   - User's email address
   - Generated reset token
   - User's full name (for personalization)

### Example Flow

```python
# User requests password reset
POST /api/v1/auth/forgot-password
{
  "email": "user@example.com"
}

# Backend creates token
token = "8Kj3nF2kL9mP1qR5sT7uV0wX2yZ4aB6cD8eF0gH2iJ4kL6mN8oP0qR2sT4uV6wX8yZ0aB2cD4eF6gH8iJ0kL2"

# Backend calls email service
POST http://localhost:8080/api/v1/send-email
{
  "to": ["user@example.com"],
  "subject": "Password Reset Request",
  "body": "Hello John,\n\nYou recently requested to reset your password..."
}

# Email service schedules and sends email
# User receives email with reset link
```

## Error Handling

### Backend Behavior

- **Service Unavailable**: If the email service is down, the endpoint still returns success (to prevent account enumeration)
- **Timeout**: 10-second timeout for email service requests
- **Logging**: All email send attempts are logged (success or failure)

### Non-Enumeration Security

The endpoint **always** returns the same response regardless of:
- Whether the email exists in the database
- Whether the email was successfully sent
- Whether the email service is available

Response:
```json
{
  "message": "If an account with that email exists, a password reset link has been sent."
}
```

## Rate Limiting

- **Forgot Password**: 3 requests per hour per IP
- **Reset Password**: 5 requests per hour per IP

## Email Templates

All email templates are in **French**.

### Password Reset Email Template

The password reset email includes:

```
Bonjour [Nom],

Vous avez récemment demandé à réinitialiser votre mot de passe. Cliquez sur le lien ci-dessous pour le réinitialiser :

[Lien de réinitialisation]

Ce lien expirera dans 30 minutes.

Si vous n'avez pas demandé de réinitialisation de mot de passe, veuillez ignorer cet e-mail ou contacter le support si vous avez des préoccupations.

Cordialement,
L'équipe de support
```

### Welcome Email Template

The welcome email for new users includes:

```
Bonjour [Nom],

Votre compte a été créé avec succès. Voici vos identifiants de connexion :

Nom d'utilisateur : [username]
Email : [email]
Mot de passe temporaire : [password]

IMPORTANT : Pour des raisons de sécurité, veuillez changer votre mot de passe lors de votre première connexion.

Vous pouvez vous connecter à l'adresse suivante :
[Login URL]

Si vous n'avez pas demandé la création de ce compte, veuillez contacter immédiatement l'administrateur système.

Cordialement,
L'équipe d'administration
```

### Customizing the Templates

To customize the email templates, modify the following functions in `app/services/email_service.py`:
- `send_password_reset_email()` - for password reset emails
- `send_welcome_email()` - for new user welcome emails

### User Creation Flow

When an administrator creates a new user via the API:

1. User provides: username, email, password, and other user details
2. Backend creates the user account with hashed password
3. Backend immediately sends a welcome email with:
   - Username
   - Email address
   - **Plain-text password** (before hashing)
   - Login URL
4. User receives email and can login with provided credentials
5. User should change password on first login (recommended)

## Testing

### Local Testing with Mock Service

You can test the integration locally by running a simple mock email service:

```python
# mock_email_service.py
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class EmailRequest(BaseModel):
    to: list[str]
    subject: str
    body: str

@app.post("/api/v1/send-email")
def send_email(request: EmailRequest):
    print(f"📧 Email scheduled:")
    print(f"   To: {request.to}")
    print(f"   Subject: {request.subject}")
    print(f"   Body: {request.body[:100]}...")
    return {"status": "scheduled", "messageId": "mock-123"}

# Run with: uvicorn mock_email_service:app --port 8080
```

### Integration Test

```python
import requests

# Test forgot password
response = requests.post(
    "http://localhost:8000/api/v1/auth/forgot-password",
    json={"email": "test@example.com"}
)
print(response.json())
# Expected: {"message": "If an account with that email exists..."}
```

## Production Deployment

### Prerequisites

1. **Java Email Service Running**: Ensure the Java cron job service is deployed and accessible
2. **Environment Variables**: Set correct URLs for your environment
3. **SMTP Configuration**: Configure the Java service with your SMTP server details
4. **Firewall Rules**: Allow traffic between FastAPI backend and Java email service

### Deployment Checklist

- [ ] Java email service deployed at `EMAIL_SERVICE_URL`
- [ ] Frontend password reset page deployed at `PASSWORD_RESET_URL`
- [ ] Environment variables configured in production
- [ ] SMTP server configured and tested
- [ ] Rate limiting verified
- [ ] Email template reviewed and approved
- [ ] Monitoring and alerting set up for email delivery

## Monitoring

### Key Metrics to Monitor

1. **Email Send Success Rate**: Track successful vs. failed email sends (by type)
2. **Email Service Availability**: Monitor uptime of Java service
3. **Response Times**: Track latency of email service API calls
4. **Token Usage**: Monitor password reset token creation and usage
5. **Rate Limit Hits**: Track how often rate limits are hit
6. **Welcome Email Delivery**: Track successful delivery of welcome emails to new users

### Log Messages

The backend logs the following events:

```python
# Password Reset Email - Success
"Password reset email scheduled for user@example.com"

# Password Reset Email - Failure
"Failed to schedule password reset email for user@example.com"

# Welcome Email - Success
"Welcome email with credentials sent to user@example.com for user 123"

# Welcome Email - Failure
"Failed to send welcome email to user@example.com for user 123. User created successfully but should be notified manually."

# Service errors
"Error connecting to email service: Connection refused"
"Timeout while connecting to email service at http://..."
```

## Security Considerations

### Password Reset Emails
1. **Non-Enumeration**: Always return the same response
2. **Token Security**: Tokens are hashed before storage
3. **Short Expiration**: 30-minute token lifetime
4. **Single-Use**: Tokens marked as used after consumption
5. **Rate Limiting**: Prevents abuse
6. **No Token Logging**: Never log the raw reset token

### Welcome Emails
1. **Password Transmission**: Plain-text passwords are sent via email (one-time only)
   - **Security Note**: This is a common practice for user onboarding, but users should be encouraged to change their password immediately
   - Consider implementing a "force password change on first login" feature
2. **Email Security**: Use TLS/SSL for SMTP communication
3. **Credential Logging**: Avoid logging plain passwords in application logs
4. **Secure Channels**: Emails should only be sent to verified email addresses

### General
1. **HTTPS**: Use HTTPS in production for email service calls
2. **Authentication**: Consider adding authentication between FastAPI and Java service
3. **Encryption**: Ensure SMTP uses TLS/SSL encryption

## Troubleshooting

### Email Not Received

1. Check if email service is running: `curl http://localhost:8080/health`
2. Check backend logs for email send attempts
3. Check Java service logs for email delivery status
4. Verify SMTP configuration in Java service
5. Check spam folder

### Connection Errors

```
Error connecting to email service: [Errno 111] Connection refused
```

**Solution**: Ensure Java email service is running and accessible at the configured URL.

### Timeout Errors

```
Timeout while connecting to email service at http://localhost:8080
```

**Solution**: 
- Check if email service is overloaded
- Increase timeout in `email_service.py` if needed
- Scale email service horizontally

## Future Enhancements

1. **HTML Email Templates**: Add support for rich HTML emails
2. **Email Queue Dashboard**: Monitor pending/sent emails
3. **Retry Logic**: Implement exponential backoff for failed sends
4. **Multiple Languages**: Support internationalized email templates
5. **Background Tasks**: Use FastAPI BackgroundTasks for better performance
6. **Callback Handler**: Implement endpoint to receive delivery status from Java service

