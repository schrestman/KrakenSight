import subprocess
import os
import logging
import math
import time
from datetime import datetime
from typing import Dict, Any

from app.modules import image as image_fetcher

logger = logging.getLogger(__name__)

DEFAULT_BG_IMAGE = "/root/.backgrounds/Solid_Orange.jpg"
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" # Debian based
OUTPUT_DIR = "/tmp"

def update_display(image_path: str):
    """
    Calls liquidctl to push the generated image to the Kraken display.
    """
    cmd = ["liquidctl", "--match", "NZXT Kraken 2024 Elite RGB", "set", "lcd", "screen", "gif", image_path]
    
    # Try up to 2 times to prevent tearing / partial uploads
    for attempt in range(2):
        try:
            logger.info(f"Pushing {image_path} to Kraken Elite... (Attempt {attempt+1})")
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info("Successfully updated display.")
            return
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to update Kraken display: {e.stderr}")
            time.sleep(1) # Wait a second before retrying
            
    logger.error("Failed to update display after multiple attempts.")

def generate_transition(prev_path: str, next_path: str, trans_type: str, frames: int) -> str:
    """
    Generates a transition GIF between two static images.
    """
    if not prev_path or not os.path.exists(prev_path):
        return None
        
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    output_path = os.path.join(OUTPUT_DIR, f"transition_{timestamp}.gif")
    
    try:
        if trans_type == "dissolve":
            # -morph generates N intermediate frames
            cmd = f'convert "{prev_path}" "{next_path}" -morph {frames} -delay 3 -loop 0 "{output_path}"'
            subprocess.run(cmd, shell=True, check=True)
            return output_path
        elif trans_type == "slide_left":
            # More complex: manual frame generation for sliding
            cmd = f'convert -delay 3 -loop 0 '
            for i in range(frames + 1):
                offset = int(640 * (i / frames))
                # Image 1 moves out to the left, Image 2 moves in from the right
                cmd += f'\\( -size 640x640 xc:black -page -{offset}+0 "{prev_path}" -page +{640-offset}+0 "{next_path}" -layers merge \\) '
            cmd += f'"{output_path}"'
            subprocess.run(cmd, shell=True, check=True)
            return output_path
        elif trans_type == "slide_right":
            cmd = f'convert -delay 3 -loop 0 '
            for i in range(frames + 1):
                offset = int(640 * (i / frames))
                cmd += f'\\( -size 640x640 xc:black -page +{offset}+0 "{prev_path}" -page -{640-offset}+0 "{next_path}" -layers merge \\) '
            cmd += f'"{output_path}"'
            subprocess.run(cmd, shell=True, check=True)
            return output_path
    except Exception as e:
        logger.error(f"Error generating transition: {e}")
        
    return None

def render_image_for_module(module_name: str, data: Dict[str, Any], module_config: Dict[str, Any] = None, global_config: Dict[str, Any] = None) -> str:
    """
    Uses ImageMagick to compose an image based on the module and data.
    """
    if module_config is None:
        module_config = {}
    if global_config is None:
        global_config = {}
        
    # Use a timestamp to ensure the file is unique and fresh to avoid read/write collisions
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    titles = module_config.get("titles", [])
    
    # Fonts and effects
    title_font_size = module_config.get("title_font_size", 40)
    text_font_size = module_config.get("text_font_size", 50)
    
    font_dir = global_config.get("default_font_dir", "/usr/share/fonts/truetype/dejavu/")
    font_name = module_config.get("font_title", global_config.get("default_font", "DejaVuSans-Bold.ttf"))
    active_font_path = os.path.join(font_dir, font_name)
    
    font_color = module_config.get("font_color", global_config.get("default_font_color", "white"))
    effect_type = module_config.get("effect_type", global_config.get("default_effect_type", "shadow")) # "shadow", "border", "none"
    effect_color = module_config.get("effect_color", global_config.get("default_effect_color", "black"))
    
    # Determine the background:
    # 1. Module override, 2. Global default, 3. Fallback color
    bg = module_config.get("background_image") or global_config.get("default_background") or "xc:black"
    
    # Check if the background string is an http/https URL. If so, dynamically download it.
    if bg.startswith("http://") or bg.startswith("https://"):
        logger.info(f"Background override is a URL. Fetching {bg}...")
        downloaded = image_fetcher.fetch_data({"url": bg})
        if downloaded.get("image_path"):
            bg = downloaded["image_path"]
        else:
            logger.warning(f"Failed to download background URL, falling back to black.")
            bg = "xc:black"
    
    # If the background is an actual file, we quote it for ImageMagick, if it's an 'xc:color', we don't
    bg_layer = f'"{bg}"' if "/" in bg or "\\" in bg else bg

    # --- Text Rendering Helpers ---
    def get_annotate_cmd(text, size, gravity, x_off, y_off):
        base_cmd = f'-font "{active_font_path}" -pointsize {size} -gravity {gravity} '
        if effect_type == "shadow":
            return base_cmd + f'-fill "{effect_color}" -annotate +{x_off+3}+{y_off+3} "{text}" -fill "{font_color}" -annotate +{x_off}+{y_off} "{text}" '
        elif effect_type == "border":
            return base_cmd + f'-stroke "{effect_color}" -strokewidth 3 -fill "{font_color}" -annotate +{x_off}+{y_off} "{text}" '
        else:
            return base_cmd + f'-fill "{font_color}" -annotate +{x_off}+{y_off} "{text}" '

    def get_caption_cmd(text, size, width, height, x_off=0, y_off=0):
        if effect_type == "shadow":
            return f'\\( -size {width}x{height} -background None -fill "{effect_color}" -font "{active_font_path}" -pointsize {size} -gravity center caption:"{text}" -geometry +{x_off+3}+{y_off+3} \\) -gravity center -composite \\( -size {width}x{height} -background None -fill "{font_color}" -font "{active_font_path}" -pointsize {size} -gravity center caption:"{text}" -geometry +{x_off}+{y_off} \\) -gravity center -composite '
        elif effect_type == "border":
            return f'\\( -size {width}x{height} -background None -stroke "{effect_color}" -strokewidth 3 -fill "{font_color}" -font "{active_font_path}" -pointsize {size} -gravity center caption:"{text}" -geometry +{x_off}+{y_off} \\) -gravity center -composite '
        else:
            return f'\\( -size {width}x{height} -background None -fill "{font_color}" -font "{active_font_path}" -pointsize {size} -gravity center caption:"{text}" -geometry +{x_off}+{y_off} \\) -gravity center -composite '

    # Generate the text annotation for all titles
    title_cmd = ""
    for t in titles:
        text = t.get("text", "")
        pos = t.get("position", "top").lower()
        if text:
            gravity = "north" if pos == "top" else "south" if pos == "bottom" else "center"
            y_off = 65 if pos in ["top", "bottom"] else 0
            title_cmd += get_annotate_cmd(text, title_font_size, gravity, 0, y_off)

    output_path = os.path.join(OUTPUT_DIR, f"{module_name}_{timestamp}.png")

    if module_name == "weather":
        temp = data.get("temp", "N/A")
        desc = data.get("description", "Unknown")
        icon_path = data.get("icon_path")
        
        weather_text = f"{temp}°C\\n{desc}"
        
        if icon_path and os.path.exists(icon_path):
            text_cmd = get_annotate_cmd(weather_text, text_font_size, "center", 0, 120)
            cmd = f'convert {bg_layer} -resize 640x640^ -gravity center -extent 640x640 \\( "{icon_path}" -resize 200x200 \\) -geometry +0-100 -composite {text_cmd} {title_cmd} "{output_path}"'
        else:
            text_cmd = get_annotate_cmd(weather_text, text_font_size, "center", 0, 0)
            cmd = f'convert {bg_layer} -resize 640x640^ -gravity center -extent 640x640 {text_cmd} {title_cmd} "{output_path}"'
            
        subprocess.run(cmd, shell=True, check=True)
        return output_path

    elif module_name == "grafana":
        graph_path = data.get("graph_image_path")
        if graph_path and os.path.exists(graph_path):
            cmd = f'convert {bg_layer} -resize 640x640^ -gravity center -extent 640x640 \\( "{graph_path}" -resize 450x450\\> \\) -gravity center -composite {title_cmd} "{output_path}"'
            subprocess.run(cmd, shell=True, check=True)
            return output_path
        else:
            logger.error("No valid graph image path provided for Grafana module.")
            return None

    elif module_name == "sysstats":
        format_lines = module_config.get("format", [
            "CPU: {cpu_percent}%",
            "RAM: {ram_used_gb}GB ({ram_percent}%)",
            "Disk: {disk_percent}%"
        ])
        
        lines = []
        for line in format_lines:
            try:
                lines.append(line.format(**data))
            except KeyError:
                lines.append(line)
        
        text = "\\n".join(lines)
        text_cmd = get_annotate_cmd(text, text_font_size, "center", 0, 0)
        
        cmd = f'convert {bg_layer} -resize 640x640^ -gravity center -extent 640x640 {text_cmd} {title_cmd} "{output_path}"'
        subprocess.run(cmd, shell=True, check=True)
        return output_path

    elif module_name == "liquidctl":
        format_lines = module_config.get("format", [
            "Liquid: {liquid_temperature}°C",
            "Pump: {pump_speed} RPM",
            "Fan: {fan_speed} RPM"
        ])
        
        lines = []
        for line in format_lines:
            try:
                lines.append(line.format(**data))
            except KeyError:
                lines.append(line)
        
        text = "\\n".join(lines)
        text_cmd = get_annotate_cmd(text, text_font_size, "center", 0, 0)
        
        cmd = f'convert {bg_layer} -resize 640x640^ -gravity center -extent 640x640 {text_cmd} {title_cmd} "{output_path}"'
        subprocess.run(cmd, shell=True, check=True)
        return output_path

    elif module_name == "clock":
        clock_type = module_config.get("clock_type", "digital")
        time_str = data.get("time_str", "00:00")
        date_str = data.get("date_str", "")
        
        if clock_type == "analog":
            duration = int(module_config.get("duration", 5))
            h_base = data.get("hour", 0)
            m_base = data.get("minute", 0)
            s_base = data.get("second", 0)
            
            output_path = os.path.join(OUTPUT_DIR, f"{module_name}_{timestamp}.gif")
            cx, cy = 320, 320
            
            cmd = f'convert -delay 100 -dispose Background '
            
            for i in range(duration+2):
                curr_time = s_base + i
                curr_s = curr_time % 60
                curr_m = (m_base + (curr_time // 60)) % 60
                curr_h = (h_base + ((m_base + (curr_time // 60)) // 60)) % 12
                
                h_angle = math.radians((curr_h % 12 + curr_m / 60) * 30 - 90)
                m_angle = math.radians((curr_m + curr_s / 60) * 6 - 90)
                s_angle = math.radians(curr_s * 6 - 90)
                
                hx, hy = cx + 130 * math.cos(h_angle), cy + 130 * math.sin(h_angle)
                mx, my = cx + 190 * math.cos(m_angle), cy + 190 * math.sin(m_angle)
                sx, sy = cx + 210 * math.cos(s_angle), cy + 210 * math.sin(s_angle)
                
                draw = f'-stroke black -strokewidth 16 -draw "line {cx},{cy} {hx},{hy}" '
                draw += f'-stroke "{font_color}" -strokewidth 12 -draw "line {cx},{cy} {hx},{hy}" '
                draw += f'-stroke black -strokewidth 12 -draw "line {cx},{cy} {mx},{my}" '
                draw += f'-stroke "{font_color}" -strokewidth 8 -draw "line {cx},{cy} {mx},{my}" '
                draw += f'-stroke red -strokewidth 4 -draw "line {cx},{cy} {sx},{sy}" '
                draw += f'-fill "{font_color}" -stroke none -draw "circle {cx},{cy} {cx+8},{cy}" '
                
                for j in range(12):
                    angle = math.radians(j * 30)
                    x1, y1 = cx + 220 * math.cos(angle), cy + 220 * math.sin(angle)
                    x2, y2 = cx + 240 * math.cos(angle), cy + 240 * math.sin(angle)
                    draw += f'-stroke "rgba(255,255,255,0.5)" -strokewidth 4 -draw "line {x1},{y1} {x2},{y2}" '
                
                cmd += f'\\( {bg_layer} -resize 640x640^ -gravity center -extent 640x640 {draw} {title_cmd} \\) '
            
            cmd += f'-loop 0 "{output_path}"'
            subprocess.run(cmd, shell=True, check=True)
            return output_path
        else: # digital
            text_fs = module_config.get("text_font_size", 120)
            date_fs = module_config.get("date_font_size", 40)
            
            time_cmd = get_annotate_cmd(time_str, text_fs, "center", 0, -20)
            date_cmd = get_annotate_cmd(date_str, date_fs, "center", 0, 80)
            
            cmd = f'convert {bg_layer} -resize 640x640^ -gravity center -extent 640x640 {time_cmd} {date_cmd} {title_cmd} "{output_path}"'
            subprocess.run(cmd, shell=True, check=True)
            return output_path

    elif module_name == "ollama":
        message = data.get("message", "Loading AI Insight...")
        caption_cmd = get_caption_cmd(message, text_font_size, 480, 480, 0, 0)
        
        cmd = f'convert {bg_layer} -resize 640x640^ -gravity center -extent 640x640 {caption_cmd} {title_cmd} "{output_path}"'
        subprocess.run(cmd, shell=True, check=True)
        return output_path

    elif module_name == "image":
        img_path = data.get("image_path")
        if img_path and os.path.exists(img_path):
            cmd = f'convert "{img_path}" -resize 640x640^ -gravity center -extent 640x640 {title_cmd} "{output_path}"'
            subprocess.run(cmd, shell=True, check=True)
            return output_path
        else:
            logger.error("No valid image path provided for image module.")
            return None

    elif module_name == "notification":
        message = data.get("message", "Notification")
        caption_cmd = get_caption_cmd(message, 40, 450, 450, 0, 0)
        
        cmd = f'convert {bg_layer} -resize 640x640^ -gravity center -extent 640x640 {caption_cmd} {title_cmd} "{output_path}"'
        subprocess.run(cmd, shell=True, check=True)
        return output_path

    logger.warning(f"No render logic for module: {module_name}")
    return None
