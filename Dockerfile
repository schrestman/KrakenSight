FROM python:3.11-slim

# Install system dependencies, including ImageMagick and fonts
RUN apt-get update && apt-get install -y \
    imagemagick \
    fonts-dejavu \
    usbutils \
    build-essential \
    libi2c-dev \
    && rm -rf /var/lib/apt/lists/*

# Fix ImageMagick policy to allow PDF/Ghostscript and other reads if necessary
# RUN sed -i 's/rights="none" pattern="PDF"/rights="read|write" pattern="PDF"/g' /etc/ImageMagick-6/policy.xml

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app /app/app
COPY config /app/config
COPY kraken.py /app/kraken.py

# Ensure there's a background directory
RUN mkdir -p /root/.backgrounds/
# Create a placeholder solid background
RUN convert -size 640x640 xc:orange /root/.backgrounds/Solid_Orange.jpg

ENV PYTHONPATH=/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

