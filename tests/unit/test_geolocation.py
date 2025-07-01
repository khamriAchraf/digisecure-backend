from unittest.mock import MagicMock, patch

import pytest

from app.utils.geolocation import GeolocationService


@pytest.fixture
def geolocation_service():
    # Use a fresh instance for each test
    return GeolocationService()


@pytest.mark.unit
def test_private_ip_detection(geolocation_service):
    # Private IPs
    assert geolocation_service._is_private_ip("127.0.0.1")
    assert geolocation_service._is_private_ip("localhost")
    assert geolocation_service._is_private_ip("::1")
    assert geolocation_service._is_private_ip("10.0.0.5")
    assert geolocation_service._is_private_ip("172.16.0.1")
    assert geolocation_service._is_private_ip("172.31.255.255")
    assert geolocation_service._is_private_ip("192.168.1.1")
    # Public IPs
    assert not geolocation_service._is_private_ip("8.8.8.8")
    assert not geolocation_service._is_private_ip("1.1.1.1")
    assert not geolocation_service._is_private_ip("100.64.0.1")


@pytest.mark.unit
def test_returns_local_network_for_private_ip(geolocation_service):
    assert geolocation_service.get_location_from_ip_sync("127.0.0.1") == "Local Network"
    assert geolocation_service.get_location_from_ip_sync("10.0.0.1") == "Local Network"
    assert (
        geolocation_service.get_location_from_ip_sync("192.168.1.1") == "Local Network"
    )
    assert geolocation_service.get_location_from_ip_sync("localhost") == "Local Network"


@pytest.mark.unit
def test_returns_unknown_for_invalid_ip(geolocation_service):
    assert geolocation_service.get_location_from_ip_sync("999.999.999.999") == "Unknown"
    assert geolocation_service.get_location_from_ip_sync("") == "Unknown"
    assert geolocation_service.get_location_from_ip_sync("not_an_ip") == "Unknown"


@pytest.mark.unit
def test_city_country_identification(geolocation_service):
    with patch.object(geolocation_service, "reader") as mock_reader:
        mock_response = MagicMock()
        mock_response.city.name = "Paris"
        mock_response.country.name = "France"
        mock_reader.city.return_value = mock_response
        assert (
            geolocation_service.get_location_from_ip_sync("8.8.8.8") == "Paris, France"
        )


@pytest.mark.unit
def test_country_only_identification(geolocation_service):
    with patch.object(geolocation_service, "reader") as mock_reader:
        mock_response = MagicMock()
        mock_response.city.name = None
        mock_response.country.name = "United States"
        mock_reader.city.return_value = mock_response
        assert (
            geolocation_service.get_location_from_ip_sync("8.8.4.4") == "United States"
        )


@pytest.mark.unit
def test_unknown_when_no_city_country(geolocation_service):
    with patch.object(geolocation_service, "reader") as mock_reader:
        mock_response = MagicMock()
        mock_response.city.name = None
        mock_response.country.name = None
        mock_reader.city.return_value = mock_response
        assert geolocation_service.get_location_from_ip_sync("9.9.9.9") == "Unknown"


@pytest.mark.unit
def test_address_not_found_error(geolocation_service):
    from geoip2.errors import AddressNotFoundError

    with patch.object(geolocation_service, "reader") as mock_reader:
        mock_reader.city.side_effect = AddressNotFoundError("Not found")
        assert geolocation_service.get_location_from_ip_sync("203.0.113.1") == "Unknown"


@pytest.mark.unit
def test_reader_not_loaded(monkeypatch):
    service = GeolocationService()
    service.reader = None
    monkeypatch.setattr(service, "_load_db", lambda: None)
    assert service.get_location_from_ip_sync("8.8.8.8") == "Unknown"


@pytest.mark.unit
def test_reader_load_failure(monkeypatch):
    with patch("geoip2.database.Reader", side_effect=Exception("fail")):
        service = GeolocationService()
        assert service.reader is None
        assert service.get_location_from_ip_sync("8.8.8.8") == "Unknown"
