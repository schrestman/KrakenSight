import psutil
import logging

logger = logging.getLogger(__name__)

def fetch_data(config: dict) -> dict:
    """
    Fetches system statistics using psutil.
    """
    try:
        # We use a short interval for CPU percent to get a quick reading instead of blocking long, 
        # or it can be 0 without interval. 
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # Calculate values and return a comprehensive dictionary
        # that can be used for string formatting.
        return {
            "cpu_percent": f"{cpu:.1f}",
            "ram_percent": f"{mem.percent:.1f}",
            "ram_used_gb": f"{mem.used / (1024**3):.1f}",
            "ram_total_gb": f"{mem.total / (1024**3):.1f}",
            "disk_percent": f"{disk.percent:.1f}",
            "disk_used_gb": f"{disk.used / (1024**3):.1f}",
            "disk_total_gb": f"{disk.total / (1024**3):.1f}",
            "disk_free_gb": f"{disk.free / (1024**3):.1f}",
        }
    except Exception as e:
        logger.error(f"Error fetching sysstats: {e}")
        return {}
