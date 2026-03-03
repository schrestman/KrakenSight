import requests
import logging
import os

logger = logging.getLogger(__name__)

def fetch_data(config: dict) -> dict:
    """
    Downloads an image of a Grafana panel using the Grafana Image Renderer.
    Requires 'url' (to the render endpoint), 'api_key', 'panel_id', etc.
    """
    base_url = config.get("url")
    api_key = config.get("api_key")
    dashboard_uid = config.get("dashboard_uid")
    panel_id = config.get("panel_id")
    
    # Time frame settings
    from_time = config.get("from", "now-1h")
    to_time = config.get("to", "now")

    if not all([base_url, api_key, dashboard_uid, panel_id]):
        logger.warning("Grafana module configuration missing parameters.")
        return {}

    # Unique download path based on panel_id or a unique key if available
    download_path = f"/tmp/grafana_panel_{panel_id}.png"

    # Example URL: http://grafana:3000/render/d-solo/<uid>?panelId=<id>&width=640&height=640
    render_url = f"{base_url}/render/d-solo/{dashboard_uid}?panelId={panel_id}&width=640&height=640&theme=dark&from={from_time}&to={to_time}"
    
    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    try:
        response = requests.get(render_url, headers=headers, stream=True, timeout=15)
        response.raise_for_status()

        # Save the image to the temporary path
        with open(download_path, 'wb') as f:
             for chunk in response.iter_content(chunk_size=8192):
                 f.write(chunk)

        logger.info(f"Successfully fetched Grafana panel {panel_id} ({from_time} to {to_time}).")
        return {"graph_image_path": download_path}

    except requests.RequestException as e:
        logger.error(f"Error fetching Grafana panel: {e}")
        return {}
