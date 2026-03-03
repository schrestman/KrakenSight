# Using KrakenSight

KrakenSight is a highly customizable daemon that rotates through various informative "modules" on your NZXT Kraken Elite display. 

This guide explains how to configure the `config/config.json` file to customize your display rotation, add titles, change fonts, and configure each specific module type.

---

## Global Configuration

At the root of your `config.json`, you define the global settings and the order in which modules will be displayed.

```json
{
    "display_interval": 10,
    "default_background": "xc:black",
    "default_font_dir": "/usr/share/fonts/truetype/dejavu/",
    "default_font": "DejaVuSans-Bold.ttf",
    "default_font_color": "white",
    "default_effect_type": "shadow",
    "default_effect_color": "black",
    "enabled_modules": ["clock_1", "weather_home", "ai_quote"]
}
```

*   `display_interval`: (Integer) The default number of seconds a module stays on the screen before cycling to the next one.
*   `default_background`: (String) The default background layer. Can be a solid color (e.g., `"xc:black"`, `"xc:blue"`) or an absolute path to a local image file.
*   `default_font_dir`: (String) The directory where your TTF/OTF fonts are located.
*   `default_font`: (String) The filename of the default font to use.
*   `default_font_color`: (String) The default color of the text. Can be a color name (e.g., `"white"`, `"cyan"`) or a hex code (e.g., `"#FFFFFF"`).
*   `default_effect_type`: (String) The text effect. Options are `"shadow"`, `"border"`, or `"none"`.
*   `default_effect_color`: (String) The color of the shadow or border effect.
*   `enabled_modules`: (List of Strings) **Critical.** This determines exactly which configuration blocks are loaded and the exact order they are displayed in. The names here must match the keys of the module blocks below.

---

## Universal Module Settings

Every module block you define can optionally include these universal overrides:

```json
"my_module_name": {
    "type": "weather", // Specifies which code handles this block
    "duration": 15,    // Overrides the global 'display_interval' for this module only
    "background_image": "/path/to/image.jpg", // Overrides 'default_background'
    "font_title": "Arial.ttf", // Overrides the global 'default_font'
    "font_color": "yellow", // Overrides 'default_font_color'
    "effect_type": "border", // Overrides 'default_effect_type'
    "effect_color": "blue", // Overrides 'default_effect_color'
    "title_font_size": 40,
    "text_font_size": 50,
    
    // Multiple titles can be drawn on the image
    "titles": [
        {"text": "Top Title", "position": "top"},
        {"text": "Bottom Title", "position": "bottom"}
    ]
}
```
*Note: Valid positions for titles are `"top"`, `"bottom"`, and `"center"`.*

---

## Module Types & Specific Configurations

You can include multiple instances of the same module type by giving them unique names and using the `"type"` parameter to tell KrakenSight how to render them.

### 1. Clock (`"type": "clock"`)
Displays a real-time clock.

*   `clock_type`: `"digital"` or `"analog"`
*   `timezone`: A standard tz database name (e.g., `"America/Chicago"`, `"Europe/London"`). Defaults to UTC.
*   `use_24h`: (Boolean) `true` for 24-hour format, `false` for 12-hour AM/PM format (Digital only).
*   *Note on Analog:* The analog clock dynamically generates a smooth, multi-frame GIF showing the second hand ticking in real-time based on the module's `duration`.

### 2. Weather (`"type": "weather"`)
Fetches current weather conditions and the official icon from OpenWeatherMap.

*   `api_key`: Your OpenWeatherMap API Key.
*   `city`: The city name (e.g., `"London"`, `"Houston, TX"`).
*   `update_interval_minutes`: (Integer) How often to poll the API (Defaults to 60).

### 3. System Stats (`"type": "sysstats"`)
Displays the host computer's CPU, RAM, and Disk usage.

*   `format`: A list of strings. Each string represents a line of text on the screen.
    *   **Available Variables:** `{cpu_percent}`, `{ram_percent}`, `{ram_used_gb}`, `{ram_total_gb}`, `{disk_percent}`, `{disk_used_gb}`, `{disk_total_gb}`, `{disk_free_gb}`
*   *Example Format:*
    ```json
    "format": [
        "CPU: {cpu_percent}%",
        "RAM: {ram_used_gb} / {ram_total_gb} GB",
        "Disk: {disk_percent}% Full"
    ]
    ```

### 4. Hardware Stats (`"type": "liquidctl"`)
Fetches and displays hardware statistics directly from your cooler (or other devices supported by `liquidctl`), such as liquid temperature and pump/fan speeds.

*   `match`: (String, Optional) A string to filter devices if you have multiple `liquidctl`-compatible devices (e.g., `"Kraken"`).
*   `format`: A list of strings acting as a template.
    *   **Available Variables:** Keys are dynamically generated from `liquidctl status` output by converting spaces to underscores and making them lowercase. 
    *   *Examples:* `{liquid_temperature}`, `{pump_speed}`, `{pump_duty}`, `{fan_speed}`, `{fan_duty}`
*   *Example Format:*
    ```json
    "format": [
        "Liquid Temp: {liquid_temperature}°C",
        "Pump: {pump_speed} RPM",
        "Fan: {fan_speed} RPM"
    ]
    ```

### 5. Grafana (`"type": "grafana"`)
Downloads a specific dashboard panel as an image. *(Requires the Grafana Image Renderer plugin).*

*   `url`: The base URL of your Grafana instance (e.g., `"http://192.168.1.100:3000"`).
*   `api_key`: A Grafana Service Account Token with viewing permissions.
*   `dashboard_uid`: The unique ID string from the dashboard's URL.
*   `panel_id`: (Integer) The specific ID of the panel (found by inspecting the panel in Grafana).
*   `from`: (String, Optional) Grafana relative time (e.g., `"now-6h"`, `"now-7d"`).
*   `to`: (String, Optional) Grafana relative time (e.g., `"now"`).

### 5. AI Insight (`"type": "ollama"`)
Sends a prompt to a local Ollama instance and displays the generated response. It automatically injects current system and weather data into the prompt for dynamic context.

*   `url`: The URL to the Ollama generate API (e.g., `"http://172.17.0.1:11434/api/generate"`).
*   `model`: The name of the locally installed model (e.g., `"llama3"`, `"gemma3:4b"`).
*   `prompt`: The instructions for the AI.
    *   **Injectable Variables:** `{weather_desc}`, `{temp}`, `{cpu_percent}`, `{ram_percent}`
*   `update_interval_minutes`: (Integer) How often to generate a new thought. Generation can be slow, so polling every 10-60 minutes is recommended.

### 6. Image Viewer (`"type": "image"`)
Displays a static image, either from the local filesystem or downloaded from the web.

*   `path`: (String, Optional) Absolute path to a local image file.
*   `url`: (String, Optional) URL to download an image from (e.g., `"https://picsum.photos/640/640"`).
*   *Note: If both are provided, `path` takes precedence.*

---

## Overriding the Display via API

KrakenSight runs a web server on port `8000` (or `8001` depending on your `docker-compose.yml` mapping). You can pause the normal rotation and instantly push a system notification to the screen by sending a POST request.

The `/api/notify` endpoint accepts a JSON payload with the following properties:
*   `message` (Required, String): The main text to display in the center of the screen.
*   `duration` (Optional, Integer): Seconds to display the notification. Defaults to 5.
*   `background_image` (Optional, String): A local file path, a URL, or an ImageMagick color (e.g. `xc:red`). Overrides the global default.
*   `font_title` (Optional, String): The name of a TTF font in your configured font directory.
*   `font_color` (Optional, String): Font color (e.g., `"white"`, `"#FFFF00"`).
*   `effect_type` (Optional, String): Text effect (`"shadow"`, `"border"`, or `"none"`).
*   `effect_color` (Optional, String): Color of the shadow/border effect.
*   `title_font_size` (Optional, Integer): Font size for the titles.
*   `text_font_size` (Optional, Integer): Font size for the main notification `message`.
*   `titles` (Optional, List of Objects): Add extra top/bottom headers to the notification just like standard modules.

**Basic Example:**
```bash
curl -X POST http://localhost:8001/api/notify \
     -H "Content-Type: application/json" \
     -d '{"message": "Deployment Successful!", "duration": 8, "background_image": "xc:green"}'
```

**Advanced Example with Custom Fonts and Titles:**
```bash
curl -X POST http://localhost:8001/api/notify \
     -H "Content-Type: application/json" \
     -d '{
           "message": "Git Push Completed",
           "duration": 10,
           "background_image": "https://picsum.photos/640/640",
           "font_title": "Courier.ttf",
           "text_font_size": 60,
           "titles": [
             {"text": "CI/CD Pipeline", "position": "top"},
             {"text": "Status: OK", "position": "bottom"}
           ]
         }'
```

Once the `duration` (in seconds) expires, KrakenSight will automatically resume its normal configured rotation.

```
