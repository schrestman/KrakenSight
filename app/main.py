import json
from datetime import datetime, timedelta
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
import uvicorn
import logging

from app.api import routes
from app.display import update_display, render_image_for_module
from app.modules import weather, grafana, sysstats, ollama_module, clock, image, liquidctl_module

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="KrakenSight API")
app.include_router(routes.router)

scheduler = BackgroundScheduler()

# Store caches for dynamically loaded modules keyed by their config name
current_module_index = 0
weather_caches = {}
ollama_caches = {}

def load_config():
    try:
        with open("/app/config/config.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("config.json not found, using default empty config.")
        return {}

def update_weather_cache(module_key: str):
    """
    Job to fetch weather data for a specific config instance.
    """
    global weather_caches
    logger.info(f"Fetching weather update for {module_key}...")
    config = load_config()
    module_config = config.get(module_key, {})
    weather_data = weather.fetch_data(module_config)
    if weather_data:
        weather_caches[module_key] = weather_data

def update_ollama_cache(module_key: str):
    """
    Job to generate a new AI response for a specific config instance.
    """
    global ollama_caches
    global weather_caches
    
    logger.info(f"Generating new Ollama insight for {module_key}...")
    config = load_config()
    ollama_config = config.get(module_key, {})
    
    if not ollama_config:
        return
        
    # Provide the first available weather cache as generic context
    context = {}
    if weather_caches:
        first_weather = next(iter(weather_caches.values()))
        context = {
            "weather_desc": first_weather.get("description", "Unknown"), 
            "temp": first_weather.get("temp", "Unknown")
        }
    
    # Get current sysstats quickly for context
    try:
        stats = sysstats.fetch_data({})
        context.update(stats)
    except Exception:
        pass
        
    ai_data = ollama_module.fetch_data(ollama_config, context)
    if ai_data:
        ollama_caches[module_key] = ai_data

def cycle_display():
    """
    Called periodically by the scheduler.
    Rotates through available modules and updates the display, then schedules itself for the next run based on module config.
    """
    global current_module_index
    config = load_config()
    
    # If there's an active override, we skip the normal rotation.
    if getattr(app.state, "override_active", False):
        logger.info("Override is active, skipping regular cycle.")
        # Check again in a few seconds
        scheduler.add_job(cycle_display, 'date', run_date=datetime.now() + timedelta(seconds=5))
        return

    modules_list = config.get("enabled_modules", [])
    if not modules_list:
        logger.warning("No modules enabled in config.")
        scheduler.add_job(cycle_display, 'date', run_date=datetime.now() + timedelta(seconds=10))
        return

    # Ensure index is within bounds if config changed
    if current_module_index >= len(modules_list):
        current_module_index = 0
        
    module_key = modules_list[current_module_index]
    logger.info(f"Cycling to module instance: {module_key}")

    module_config = config.get(module_key, {})
    
    # Determine how long this module should be displayed
    duration = module_config.get("duration", config.get("display_interval", 10))
    
    # Determine the type of the module (defaults to the key name)
    module_type = module_config.get("type", module_key)

    try:
        if module_type == "weather":
            data = weather_caches.get(module_key, {"temp": "N/A", "description": "Loading...", "city": "N/A"})
            output_path = render_image_for_module(module_type, data, module_config, config)
        elif module_type == "grafana":
            data = grafana.fetch_data(module_config)
            output_path = render_image_for_module(module_type, data, module_config, config)
        elif module_type == "sysstats":
            data = sysstats.fetch_data(module_config)
            output_path = render_image_for_module(module_type, data, module_config, config)
        elif module_type == "ollama":
            data = ollama_caches.get(module_key, {"message": "Generating..."})
            output_path = render_image_for_module(module_type, data, module_config, config)
        elif module_type == "clock":
            data = clock.fetch_data(module_config)
            output_path = render_image_for_module(module_type, data, module_config, config)
        elif module_type == "image":
            data = image.fetch_data(module_config)
            output_path = render_image_for_module(module_type, data, module_config, config)
        elif module_type == "liquidctl":
            data = liquidctl_module.fetch_data(module_config)
            output_path = render_image_for_module(module_type, data, module_config, config)
        else:
            logger.error(f"Unknown module type '{module_type}' for config key '{module_key}'")
            output_path = None

        if output_path:
            update_display(output_path)
    except Exception as e:
        logger.error(f"Error rendering/updating {module_key}: {e}")

    # Move to the next module for the next run
    current_module_index = (current_module_index + 1) % len(modules_list)
    
    # Schedule the next execution
    scheduler.add_job(cycle_display, 'date', run_date=datetime.now() + timedelta(seconds=duration))

@app.on_event("startup")
def startup_event():
    # Load configuration
    logger.info("Starting up KrakenSight...")
    app.state.override_active = False

    config = load_config()
    
    # Initialize background jobs based on enabled modules
    for module_key in config.get("enabled_modules", []):
        module_config = config.get(module_key, {})
        module_type = module_config.get("type", module_key)
        
        if module_type == "weather":
            update_weather_cache(module_key)
            interval = module_config.get("update_interval_minutes", 60)
            scheduler.add_job(update_weather_cache, 'interval', minutes=interval, args=[module_key])
            
        elif module_type == "ollama":
            update_ollama_cache(module_key)
            interval = module_config.get("update_interval_minutes", 60)
            scheduler.add_job(update_ollama_cache, 'interval', minutes=interval, args=[module_key])

    # Kick off the first display cycle immediately
    scheduler.add_job(cycle_display)
    scheduler.start()
    logger.info("Display cycle started.")

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()
    logger.info("Daemon shut down.")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
