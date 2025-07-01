import os
from functools import lru_cache

import geoip2.database
from geoip2.errors import AddressNotFoundError

from app.core.config import settings
from app.core.logger import logger


class GeolocationService:
    """Service to resolve IP addresses to geographic locations using local GeoLite2 DB"""

    def __init__(self):
        self.db_path = settings.GEOLITE2_DB_PATH
        self.reader = None
        self._load_db()

    def _load_db(self):
        if os.path.exists(self.db_path):
            try:
                self.reader = geoip2.database.Reader(self.db_path)
            except Exception as e:
                logger.warning(f"Failed to load GeoLite2 DB: {e}")
                self.reader = None
        else:
            logger.warning(f"GeoLite2 DB not found at {self.db_path}")
            self.reader = None

    @lru_cache(maxsize=1000)
    def get_location_from_ip_sync(self, ip_address: str) -> str:
        """
        Synchronous geolocation using local GeoLite2 DB
        Args:
            ip_address: The IP address to resolve
        Returns:
            Location string in format "City, Country", "Country", "Local Network", or "Unknown"
        """
        if self._is_private_ip(ip_address):
            return "Local Network"
        if not self.reader:
            self._load_db()
        if not self.reader:
            return "Unknown"
        try:
            response = self.reader.city(ip_address)
            city = response.city.name or ""
            country = response.country.name or ""
            if city and country:
                return f"{city}, {country}"
            elif country:
                return country
            else:
                return "Unknown"
        except AddressNotFoundError:
            return "Unknown"
        except Exception as e:
            logger.warning(f"GeoLite2 lookup error for IP {ip_address}: {e}")
            return "Unknown"

    def _is_private_ip(self, ip_address: str) -> bool:
        if ip_address in ["127.0.0.1", "localhost", "::1"]:
            return True
        try:
            parts = ip_address.split(".")
            if len(parts) == 4:
                first_octet = int(parts[0])
                second_octet = int(parts[1])
                if first_octet == 10:
                    return True
                elif first_octet == 172 and 16 <= second_octet <= 31:
                    return True
                elif first_octet == 192 and second_octet == 168:
                    return True
        except (ValueError, IndexError):
            pass
        return False


# Create a global instance
geolocation_service = GeolocationService()
