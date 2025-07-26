from datetime import datetime, timezone

from app.core.logger import logger
from app.utils.geolocation import geolocation_service
from app.utils.request_utils import get_client_ip
from app.utils.user_agent_parser import parse_user_agent


def log_login_attempt(
    request, email: str, location: str = "Unknown", success: bool = True
) -> None:
    ip_address = get_client_ip(request)
    if location == "Unknown":
        location = geolocation_service.get_location_from_ip_sync(ip_address)
    user_agent = request.headers.get("User-Agent", "")
    parsed_ua = parse_user_agent(user_agent)
    log_method = logger.info if success else logger.warning
    log_method(
        "login_attempt",
        extra={
            "log_type": "auth",
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "email": email,
            "ip": ip_address,
            "location": location,
            "user_agent": user_agent,
            "device": parsed_ua["device"],
            "os": parsed_ua["os"],
            "browser": parsed_ua["browser"],
            "success": success,
        },
    )


def log_successful_login(request, user, success: bool = True) -> None:
    log_login_attempt(
        request=request,
        email=user.email,
        location=user.location or "Unknown",
        success=success,
    )
