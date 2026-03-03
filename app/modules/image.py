import os
import requests
import logging
import hashlib

logger = logging.getLogger(__name__)

def fetch_data(config: dict) -> dict:
    """
    Provides the image path from the local filesystem, or downloads it from a URL.
    """
    path = config.get("path")
    url = config.get("url")
    
    if path:
        # If it's a local file, just pass the path along
        if os.path.exists(path):
            return {"image_path": path}
        else:
            logger.warning(f"Image path not found: {path}")
            return {}
            
    if url:
        # Create a unique filename based on the URL
        url_hash = hashlib.md5(url.encode()).hexdigest()
        download_path = f"/tmp/image_{url_hash}.png"
        
        try:
            logger.info(f"Downloading image from {url}...")
            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()
            
            with open(download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return {"image_path": download_path}
        except requests.RequestException as e:
            logger.error(f"Error fetching image URL: {e}")
            return {}
            
    logger.warning("Image module configuration missing 'path' or 'url'.")
    return {}
