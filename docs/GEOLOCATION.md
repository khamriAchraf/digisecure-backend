# Geolocation Feature

## Overview

The geolocation feature uses a **local MaxMind GeoLite2 database** to resolve IP addresses to geographic locations for connection logging. This provides instant, reliable, and privacy-friendly location lookups.

## How It Works

### IP Resolution Process

1. **IP Address Extraction**: The system extracts the client IP address from the request headers, handling various proxy scenarios:
   - `X-Forwarded-For` header
   - `X-Real-IP` header  
   - `X-Client-IP` header
   - Direct client IP

2. **Private IP Detection**: Local and private IP addresses are identified and marked as "Local Network":
   - `127.0.0.1` (localhost)
   - `10.0.0.0/8` range
   - `172.16.0.0/12` range
   - `192.168.0.0/16` range

3. **Geolocation Resolution**: Public IP addresses are resolved using the **local GeoLite2 database** (no external API calls):
   - Lookups are performed using the MaxMind GeoLite2 City database (`.mmdb` file)
   - Results are cached to avoid repeated lookups

### Location Format

The resolved location is returned in the format:
- `"City, Country"` (e.g., "New York, United States")
- `"Country"` (if city is not available)
- `"Local Network"` (for private IPs)
- `"Unknown"` (if resolution fails)

## Implementation Details

### Files

- `app/utils/geolocation.py` - Core geolocation service (now local-only)
- `app/utils/connection_logger.py` - Integration with connection logging
- `app/utils/request_utils.py` - IP address extraction utilities

### Key Features

1. **Local Database**: No external API calls; all lookups are local and instant
2. **Caching**: LRU cache with 1000 entries to improve performance
3. **Error Handling**: Graceful fallback when DB is missing or lookup fails
4. **Logging**: Comprehensive logging for debugging and monitoring
5. **Configurable DB Path**: Path to the GeoLite2 database is set via `.env`/config

### Usage

The geolocation service is automatically used in the connection logger:

```python
from app.utils.connection_logger import connection_logger

connection_logger.log_login_attempt(request, username, email, success=True)
```

## Configuration

### Dependencies

The feature requires `geoip2` for reading the MaxMind database. It's included in the main dependencies:

```toml
[tool.poetry.dependencies]
geoip2 = "^4.8.0"
```

### Database Path

Set the path to your GeoLite2 database in your `.env` file:

```
GEOLITE2_DB_PATH=./data/GeoLite2-City.mmdb
```

If not set, it defaults to `./data/GeoLite2-City.mmdb`.

### Database Updates

- Download the latest GeoLite2 City database from MaxMind: https://dev.maxmind.com/geoip/geolite2-free-geolocation-data
- Place the `.mmdb` file at the path specified in your config

## Testing

Run the unit tests to verify functionality:

```bash
pytest tests/unit/test_geolocation.py
```

This will test:
- Public IP resolution (mocked)
- Private IP detection
- Caching behavior
- Error handling
- Edge cases

## Log Output Example

```json
{
  "timestamp": "2025-07-01T11:04:23.043580Z",
  "username": "john.doe",
  "email": "john.doe@example.com",
  "ip": "192.168.1.55",
  "location": "Fes, Morocco",
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
  "device": "Desktop",
  "os": "Windows 10",
  "browser": "Chrome",
  "success": true
}
```

## Security Considerations

1. **Privacy**: IP addresses are logged for security purposes
3. **GDPR Compliance**: Ensure logging practices comply with data protection regulations
4. **No External API**: All lookups are local, so no user data is sent to third parties

## Troubleshooting

### Common Issues

1. **"Unknown" Location**: 
   - Check that the GeoLite2 database file exists and is readable
   - Verify the path in your `.env` or config
   - Check for typos in the IP address

2. **Database Not Found**:
   - Download the latest `.mmdb` file and place it at the configured path

3. **Database Corruption**:
   - Download a fresh copy of the database

### Monitoring

Monitor the following metrics:
- Cache hit/miss ratios
- Error rates for lookups
- Success rates for location resolution 