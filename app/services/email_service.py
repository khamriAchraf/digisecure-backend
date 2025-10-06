"""
Email service for sending emails via external Java cron job service.
"""

from typing import List, Optional

import httpx

from app.core.config import settings
from app.core.logger import logger


async def send_email_async(
    to: List[str],
    subject: str,
    body: str,
    request_id: Optional[str] = None,
    callback_url: Optional[str] = None,
) -> bool:
    """
    Send an email via the Java cron job service (Quartz-based).

    Args:
        to: List of recipient email addresses
        subject: Email subject
        body: Email body (can be plain text or HTML)
        request_id: Optional request ID for tracking
        callback_url: Optional callback URL for job result notification

    Returns:
        True if email was scheduled successfully, False otherwise
    """
    email_service_url = f"{settings.EMAIL_SERVICE_URL}/api/v1/send-email"

    payload = {
        "to": to,
        "subject": subject,
        "body": body,
    }

    if request_id:
        payload["requestId"] = request_id

    if callback_url:
        payload["callbackUrl"] = callback_url

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                email_service_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code in [200, 201, 202]:
                logger.info(
                    f"Email scheduled successfully via cron job service: "
                    f"to={to}, subject={subject}, request_id={request_id}"
                )
                return True
            else:
                logger.error(
                    f"Failed to schedule email: status={response.status_code}, "
                    f"response={response.text}"
                )
                return False

    except httpx.TimeoutException:
        logger.error(
            f"Timeout while connecting to email service at {email_service_url}"
        )
        return False
    except httpx.RequestError as e:
        logger.error(f"Error connecting to email service: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending email: {str(e)}")
        return False


def _run_async_email(to: List[str], subject: str, body: str) -> bool:
    """
    Helper function to run async email sending from sync context.

    Args:
        to: List of recipient email addresses
        subject: Email subject
        body: Email body

    Returns:
        True if email was scheduled successfully, False otherwise
    """
    import asyncio

    try:
        # Try to get the current event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're already in an async context, create a task
            # This shouldn't happen in FastAPI sync endpoints
            logger.warning("Attempting to send email from already running event loop")
            return False
        else:
            # Run the async function in the current loop
            return loop.run_until_complete(
                send_email_async(to=to, subject=subject, body=body)
            )
    except RuntimeError:
        # No event loop exists, create a new one
        return asyncio.run(send_email_async(to=to, subject=subject, body=body))


def send_password_reset_email(
    email: str, token: str, user_full_name: Optional[str] = None
) -> bool:
    """
    Send a password reset email with the reset link (in French).

    This is a synchronous wrapper that can be called from sync endpoints.
    Note: For better performance in production, consider using background tasks.

    Args:
        email: Recipient email address
        token: Password reset token
        user_full_name: Optional user's full name for personalization

    Returns:
        True if email was scheduled successfully, False otherwise
    """
    reset_link = f"{settings.PASSWORD_RESET_URL}?token={token}"

    greeting = f"Bonjour {user_full_name}," if user_full_name else "Bonjour,"

    subject = "Demande de réinitialisation de mot de passe"
    body = f"""
{greeting}

Vous avez récemment demandé à réinitialiser votre mot de passe. Cliquez sur le lien ci-dessous pour le réinitialiser :

{reset_link}

Ce lien expirera dans {settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} minutes.

Si vous n'avez pas demandé de réinitialisation de mot de passe, veuillez ignorer cet e-mail ou contacter le support si vous avez des préoccupations.

Cordialement,
L'équipe de support
"""

    return _run_async_email(to=[email], subject=subject, body=body)


def send_welcome_email(
    email: str, username: str, password: str, user_full_name: Optional[str] = None
) -> bool:
    """
    Send a welcome email with credentials to a newly created user (in French).

    This is a synchronous wrapper that can be called from sync endpoints.

    Args:
        email: Recipient email address
        username: User's username
        password: User's temporary password (plain text)
        user_full_name: Optional user's full name for personalization

    Returns:
        True if email was scheduled successfully, False otherwise
    """
    greeting = f"Bonjour {user_full_name}," if user_full_name else "Bonjour,"

    subject = "Bienvenue - Vos identifiants de connexion"
    body = f"""
{greeting}

Votre compte a été créé avec succès. Voici vos identifiants de connexion :

Nom d'utilisateur : {username}
Email : {email}
Mot de passe temporaire : {password}

IMPORTANT : Pour des raisons de sécurité, veuillez changer votre mot de passe lors de votre première connexion.

Vous pouvez vous connecter à l'adresse suivante :
{settings.PASSWORD_RESET_URL.rsplit('/reset-password', 1)[0]}/login

Si vous n'avez pas demandé la création de ce compte, veuillez contacter immédiatement l'administrateur système.

Cordialement,
L'équipe d'administration
"""

    return _run_async_email(to=[email], subject=subject, body=body)
