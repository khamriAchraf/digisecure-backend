import json
import logging
from datetime import datetime
from pathlib import Path

from app.utils.geolocation import geolocation_service
from app.utils.request_utils import get_client_ip
from app.utils.user_agent_parser import parse_user_agent


class ConnectionLogger:
    """Logger for connection events to connection.log file"""

    def __init__(self, log_file_path: str = "logs/connection.log"):
        self.log_file_path = Path(log_file_path)
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger("connection_logger")
        self.logger.setLevel(logging.INFO)

        file_handler = logging.FileHandler(self.log_file_path, mode="a")
        file_handler.setLevel(logging.INFO)

        formatter = logging.Formatter("%(message)s")
        file_handler.setFormatter(formatter)

        if not self.logger.handlers:
            self.logger.addHandler(file_handler)

    def log_login_attempt(
        self, request, email: str, location: str = "Unknown", success: bool = True
    ) -> None:
        """
        Log a login attempt event to connection.log

        Args:
            request: FastAPI Request object
            email: Email attempting to login
            location: User location (if available)
            success: Whether the login was successful
        """
        # Get client IP
        ip_address = get_client_ip(request)

        # Get location from IP address if not provided
        if location == "Unknown":
            location = geolocation_service.get_location_from_ip_sync(ip_address)

        # Get user agent and parse it
        user_agent = request.headers.get("User-Agent", "")
        parsed_ua = parse_user_agent(user_agent)

        # Create log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "email": email,
            "ip": ip_address,
            "location": location,
            "user_agent": user_agent,
            "device": parsed_ua["device"],
            "os": parsed_ua["os"],
            "browser": parsed_ua["browser"],
            "success": success,
        }

        # Write to log file
        self.logger.info(json.dumps(log_entry))

    def log_successful_login(self, request, user, success: bool = True) -> None:
        """
        Log a successful login event to connection.log

        Args:
            request: FastAPI Request object
            user: User object from database
            success: Whether the login was successful
        """
        self.log_login_attempt(
            request=request,
            email=user.email,
            location=user.location or "Unknown",
            success=success,
        )


# Create a global instance
connection_logger = ConnectionLogger()
