from typing import Dict


def parse_user_agent(user_agent: str) -> Dict[str, str]:
    """
    Parse user agent string to extract device, OS, and browser information.

    Args:
        user_agent: The user agent string from the request

    Returns:
        Dictionary containing device, os, and browser information
    """
    if not user_agent:
        return {"device": "Unknown", "os": "Unknown", "browser": "Unknown"}

    user_agent = user_agent.lower()

    # Device detection
    device = "Other"
    if any(keyword in user_agent for keyword in ["iphone", "ipad", "ipod"]):
        device = "iOS"
    elif "android" in user_agent:
        device = "Android"
    elif "windows phone" in user_agent:
        device = "Windows Phone"
    elif "blackberry" in user_agent:
        device = "BlackBerry"
    elif any(keyword in user_agent for keyword in ["mobile", "tablet"]):
        device = "Mobile"
    elif "windows" in user_agent or "macintosh" in user_agent or "linux" in user_agent:
        device = "Desktop"

    # OS detection
    os_name = "Unknown"
    if "windows nt 10.0" in user_agent:
        os_name = "Windows 10"
    elif "windows nt 6.3" in user_agent:
        os_name = "Windows 8.1"
    elif "windows nt 6.2" in user_agent:
        os_name = "Windows 8"
    elif "windows nt 6.1" in user_agent:
        os_name = "Windows 7"
    elif "windows nt 6.0" in user_agent:
        os_name = "Windows Vista"
    elif "windows nt 5.1" in user_agent or "windows xp" in user_agent:
        os_name = "Windows XP"
    elif "windows" in user_agent:
        os_name = "Windows"
    elif "macintosh" in user_agent or "mac os x" in user_agent:
        os_name = "macOS"
    elif "linux" in user_agent:
        os_name = "Linux"
    elif "android" in user_agent:
        os_name = "Android"
    elif "iphone" in user_agent or "ipad" in user_agent or "ipod" in user_agent:
        os_name = "iOS"
    elif "blackberry" in user_agent:
        os_name = "BlackBerry"

    # Browser detection
    browser = "Unknown"
    if "firefox" in user_agent:
        browser = "Firefox"
    elif "chrome" in user_agent and "chromium" not in user_agent:
        browser = "Chrome"
    elif "safari" in user_agent and "chrome" not in user_agent:
        browser = "Safari"
    elif "edge" in user_agent:
        browser = "Edge"
    elif "opera" in user_agent:
        browser = "Opera"
    elif "chromium" in user_agent:
        browser = "Chromium"
    elif "ie" in user_agent or "internet explorer" in user_agent:
        browser = "Internet Explorer"

    return {"device": device, "os": os_name, "browser": browser}
