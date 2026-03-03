from fastapi import APIRouter, Request, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import logging

from app.display import render_image_for_module, update_display

logger = logging.getLogger(__name__)

router = APIRouter()

class Notification(BaseModel):
    message: str
    duration: int = 5  # seconds to display
    background_image: Optional[str] = None
    font_title: Optional[str] = None
    font_color: Optional[str] = None
    effect_type: Optional[str] = None
    effect_color: Optional[str] = None
    title_font_size: Optional[int] = None
    text_font_size: Optional[int] = None
    titles: Optional[List[Dict[str, str]]] = None

async def handle_override(request: Request, notif: Notification):
    """
    Temporarily overrides the regular display cycle.
    """
    request.app.state.override_active = True
    logger.info(f"Notification active for {notif.duration} seconds: {notif.message}")

    try:
        # Generate and push notification image
        module_config = {}
        if notif.background_image:
            module_config["background_image"] = notif.background_image
        if notif.font_title:
            module_config["font_title"] = notif.font_title
        if notif.font_color:
            module_config["font_color"] = notif.font_color
        if notif.effect_type:
            module_config["effect_type"] = notif.effect_type
        if notif.effect_color:
            module_config["effect_color"] = notif.effect_color
        if notif.title_font_size:
            module_config["title_font_size"] = notif.title_font_size
        if notif.text_font_size:
            module_config["text_font_size"] = notif.text_font_size
        if notif.titles:
            module_config["titles"] = notif.titles
            
        output_path = render_image_for_module("notification", {"message": notif.message}, module_config)
        if output_path:
            update_display(output_path)
            await asyncio.sleep(notif.duration)
    except Exception as e:
         logger.error(f"Error handling notification override: {e}")
    finally:
        logger.info("Notification override ending, resuming cycle.")
        request.app.state.override_active = False


@router.post("/api/notify")
async def send_notification(notif: Notification, request: Request, background_tasks: BackgroundTasks):
    """
    Endpoint to receive a system notification and display it temporarily.
    """
    # Start the override in the background so the API returns quickly
    background_tasks.add_task(handle_override, request, notif)
    return {"status": "Notification received, overriding display temporarily."}
