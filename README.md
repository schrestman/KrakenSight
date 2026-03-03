# KrakenSight

A modular Python-based daemon designed to generate and display custom dashboards on the NZXT Kraken 2024 Elite RGB liquid cooler's 640x640 LCD screen.

## Features

*   **Modular Data Fetchers**: Easily extendable to pull data from various sources.
    *   **Weather**: Fetches real-time weather data and icons from OpenWeatherMap.
    *   **Grafana**: Downloads and displays specific dashboard panels using the Grafana Image Renderer.
*   **Dynamic Image Generation**: Uses ImageMagick to compose 640x640 images with:
    *   Support for multiple custom titles (Top/Bottom/Middle).
    *   Custom backgrounds per module or a global default.
    *   Automatic scaling to fit within the circular Kraken viewport.
    *   Pronounced drop shadows for high readability.
*   **REST API**: A FastAPI-based endpoint (`POST /api/notify`) to send temporary system notifications that override the display cycle.
*   **Dockerized**: Fully containerized setup using Docker Compose for easy deployment.
*   **Daemonized Scheduler**: Rotates through configured modules at a user-defined interval.

## Prerequisites

*   NZXT Kraken 2024 Elite RGB.
*   Docker and Docker Compose installed.
*   (Optional) OpenWeatherMap API Key.
*   (Optional) Grafana instance with the `grafana-image-renderer` plugin installed.

## Setup & Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd custom_kraken
    ```

2.  **Configure the application**:
    Edit `config/config.json` with your settings:
    ```json
    {
        "display_interval": 10,
        "default_background": "xc:black",
        "weather": {
            "api_key": "YOUR_OPENWEATHERMAP_API_KEY",
            "city": "Your City",
            "titles": [
                {"text": "Local Weather", "position": "top"}
            ]
        },
        "grafana": {
            "url": "http://your-grafana:3000",
            "api_key": "YOUR_GRAFANA_TOKEN",
            "dashboard_uid": "your-uid",
            "panel_id": 1,
            "titles": [
                {"text": "Network Traffic", "position": "top"}
            ]
        }
    }
    ```

3.  **Build and start the container**:
    ```bash
    docker compose up -d --build
    ```
    *Note: The container runs in privileged mode to allow `liquidctl` access to the USB device.*

## API Usage (Notifications)

You can send temporary notifications to the display using the API:

```bash
curl -X POST http://localhost:8001/api/notify \
     -H "Content-Type: application/json" \
     -d '{"message": "Deployment Successful!", "duration": 10}'
```

## Author

**Scott Chrestman**

## License

This project is open-source and available under the MIT License.
