import requests
import logging
import os

logger = logging.getLogger(__name__)

ICON_DOWNLOAD_PATH = "/tmp/weather_icon.png"

def fetch_data(config: dict) -> dict:
    """
    Fetches current weather data from OpenWeatherMap (example).
    Needs 'api_key' and 'city' in config.
    """
    api_key = config.get("api_key")
    city = config.get("city")

    if not api_key or not city:
        logger.warning("Weather module configured without API key or city.")
        return {"temp": "N/A", "description": "No config", "city": "N/A"}

    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=imperial"
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        weather_info = {
            "temp": round(data["main"]["temp"], 1),
            "description": data["weather"][0]["description"].capitalize(),
            "city": data["name"]
        }

        # Fetch the icon
        icon_code = data["weather"][0].get("icon")
        if icon_code:
            icon_url = f"http://openweathermap.org/img/wn/{icon_code}@4x.png"
            try:
                icon_response = requests.get(icon_url, stream=True, timeout=5)
                icon_response.raise_for_status()
                with open(ICON_DOWNLOAD_PATH, 'wb') as f:
                    for chunk in icon_response.iter_content(chunk_size=8192):
                        f.write(chunk)
                weather_info["icon_path"] = ICON_DOWNLOAD_PATH
            except requests.RequestException as e:
                logger.error(f"Error fetching weather icon: {e}")

        return weather_info

    except requests.RequestException as e:
         logger.error(f"Error fetching weather: {e}")
         return {"temp": "Err", "description": "Fetch failed", "city": city}
