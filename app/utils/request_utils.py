from fastapi import Request


def get_client_ip(request: Request) -> str:
    """
    Extract the real client IP address from the request.
    Handles various proxy scenarios and headers.

    Args:
        request: FastAPI Request object

    Returns:
        Client IP address as string
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    client_ip = request.headers.get("X-Client-IP")
    if client_ip:
        return client_ip

    if request.client:
        return request.client.host

    return "Unknown"
