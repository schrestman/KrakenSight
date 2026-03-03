import subprocess
import json
import logging

logger = logging.getLogger(__name__)

def fetch_data(config: dict) -> dict:
    """
    Fetches hardware statistics using liquidctl.
    Converts keys like 'Liquid temperature' to 'liquid_temperature'.
    """
    try:
        cmd = ["liquidctl", "status", "--json"]
        
        # Optional match string if the user has multiple liquidctl devices
        match = config.get("match")
        if match:
            cmd = ["liquidctl", "--match", match, "status", "--json"]
            
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        data = json.loads(result.stdout)
        
        variables = {}
        
        # Flatten all status items into a single dictionary
        for device in data:
            status_items = device.get("status", [])
            for item in status_items:
                # Convert spaces to underscores and make lowercase for easy formatting
                key = item.get("key", "").lower().replace(" ", "_")
                val = item.get("value", "")
                variables[key] = val
                
        return variables
    except subprocess.CalledProcessError as e:
        logger.error(f"Error fetching liquidctl stats: {e.stderr}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding liquidctl json: {e}")
        return {}
    except FileNotFoundError:
        logger.error("liquidctl is not installed or not found in PATH.")
        return {}
