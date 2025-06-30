# visualization/server.py
from mcp.server import FastMCP
import json
import os
from typing import List, Dict, Any, Optional
import logging
from fastapi import Response

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create the Visualization MCP server
mcp = FastMCP(
    name="Visualization Server",
    host="0.0.0.0",
    port=8006
)

# Add a health check route directly to the MCP server
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    """
    Simple health check endpoint for ALB Target Group.
    Always returns 200 OK to indicate the service is running.
    """
    return Response(
        content="healthy",
        status_code=200,
        media_type="text/plain"
    )

# Path to the visualization data file
DATA_FILE = os.path.join(os.path.dirname(__file__), "city_images_data.json")

def load_visualization_data() -> Dict[str, Any]:
    """Load visualization data from the JSON file."""
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        else:
            logger.warning(f"Visualization data file {DATA_FILE} not found.")
            return {"cities": {}}
    except Exception as e:
        logger.error(f"Error loading visualization data: {e}")
        return {"cities": {}}

# Load visualization data
visualization_data = load_visualization_data()

@mcp.tool()
def get_city_image(city: str, image_type: str = "skyline") -> Dict[str, Any]:
    """
    Get an image URL for a specific city.
    
    Parameters:
    - city: The city to get an image for
    - image_type: Type of image (skyline, downtown, aerial, etc.)
    """
    city = city.lower().replace(" ", "_")
    image_type = image_type.lower()
    
    if city not in visualization_data.get("cities", {}):
        return {"error": "City not found"}
    
    city_data = visualization_data["cities"][city]
    
    # Map image_type to the appropriate field in the data
    image_type_mapping = {
        "skyline": "destination",
        "downtown": "destination",
        "aerial": "destination",
        "map": "map",
        "weather_chart": "weather_chart"
    }
    
    field = image_type_mapping.get(image_type, "destination")
    
    if field not in city_data:
        return {"error": "Image type not found"}
    
    image_url = city_data[field]
    
    return {
        "city": city,
        "image_type": image_type,
        "image_url": image_url
    }

@mcp.tool()
def get_attraction_image(city: str, attraction: str) -> Dict[str, Any]:
    """
    Get image URLs for a specific attraction in a city.
    
    Parameters:
    - city: The city where the attraction is located
    - attraction: The attraction to get images for
    """
    city = city.lower().replace(" ", "_")
    
    if city not in visualization_data.get("cities", {}):
        return {"error": "City not found"}
    
    city_data = visualization_data["cities"][city]
    places = city_data.get("places", {})
    
    # Try to find the attraction (case insensitive)
    attraction_key = None
    for key in places.keys():
        if key.lower() == attraction.lower():
            attraction_key = key
            break
    
    if not attraction_key:
        return {"error": "Attraction not found"}
    
    image_url = places[attraction_key]
    
    return {
        "city": city,
        "attraction": attraction_key,
        "image_url": image_url
    }

@mcp.tool()
def generate_weather_chart(city: str, weather_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate a weather chart for a city based on weather data.
    
    Parameters:
    - city: The city to generate a chart for
    - weather_data: List of weather data points with temperature, conditions, etc.
    """
    if not weather_data:
        return {"error": "No weather data provided"}
    
    city = city.lower().replace(" ", "_")
    
    if city not in visualization_data.get("cities", {}):
        return {"error": "City not found"}
    
    city_data = visualization_data["cities"][city]
    chart_url = city_data.get("weather_chart", "https://example.com/default_weather_chart.png")
    
    return {
        "city": city,
        "days": len(weather_data),
        "chart_url": chart_url
    }

@mcp.tool()
def list_available_image_types(city: str) -> Dict[str, Any]:
    """List all available image types for a specific city."""
    city = city.lower().replace(" ", "_")
    
    if city not in visualization_data.get("cities", {}):
        return {"error": "City not found"}
    
    city_data = visualization_data["cities"][city]
    available_types = []
    
    if "destination" in city_data:
        available_types.extend(["skyline", "downtown", "aerial"])
    if "map" in city_data:
        available_types.append("map")
    if "weather_chart" in city_data:
        available_types.append("weather_chart")
    
    return {
        "city": city,
        "image_types": available_types,
        "count": len(available_types)
    }

# Start the MCP server
if __name__ == "__main__":
    logger.info(f"Starting Visualization Server with {len(visualization_data.get('cities', {}))} cities")
    mcp.run(transport="streamable-http")
