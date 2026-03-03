import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from zoneinfo import ZoneInfoNotFoundError

logger = logging.getLogger(__name__)

def fetch_data(config: dict) -> dict:
    """
    Fetches the current time for the given timezone.
    """
    timezone_str = config.get("timezone", "UTC")
    try:
        tz = ZoneInfo(timezone_str)
    except ZoneInfoNotFoundError:
        logger.warning(f"Timezone {timezone_str} not found, falling back to UTC.")
        tz = ZoneInfo("UTC")
        
    now = datetime.now(tz)
    
    use_24h = config.get("use_24h", False)
    
    # Format the time string
    if use_24h:
        time_str = now.strftime("%H:%M")
    else:
        # %I has a leading zero, we can strip it for a cleaner look
        time_str = now.strftime("%I:%M %p").lstrip("0")
    
    return {
        "hour": now.hour,
        "minute": now.minute,
        "second": now.second,
        "date_str": now.strftime("%A, %B %d"),
        "time_str": time_str
    }
