import subprocess

# Settings
temp = "42"
bg_image = "/home/br0/.backgrounds/Solid_Orange.jpg"  # Path to your image
output_path = "/tmp/kraken_display.png"
font_path = "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf" # Adjust for Arch

# The ImageMagick Command
# 1. Load background and resize/crop to fill 640x640
# 2. Add text in the center
cmd = f"""
magick "{bg_image}" \
    -resize 640x640^ -gravity center -extent 640x640 \
    -fill "rgba(0,0,0,0.5)" -annotate +5+5 "{temp}°C" \
    -fill white             -annotate +0+0 "{temp}°C" \
    -fill white -font "{font_path}" -pointsize 150 \
    -gravity center -annotate +0+0 "{temp}°C" \
    "{output_path}"
"""

try:
    # Generate the image
    subprocess.run(cmd, shell=True, check=True)
    
    # Push to Kraken Elite
    #subprocess.run(["liquidctl", "set", "lcd", "screen", output_path], check=True)
    subprocess.run(["liquidctl", "--match", "NZXT Kraken 2024 Elite RGB", "set", "lcd", "screen", "gif", output_path], check=True)
    print(f"Successfully updated Kraken with temp: {temp}°C")
except subprocess.CalledProcessError as e:
    print(f"Error updating display: {e}")
