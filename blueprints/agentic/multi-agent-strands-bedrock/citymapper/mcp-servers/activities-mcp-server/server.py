"""Activities MCP Server - Travel activities and destinations server."""

import os
import json
import argparse
from typing import Any, Dict, List
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("activities")

# Data loading
DATA_FILE = os.path.join(os.path.dirname(__file__), "activities_data.json")

def load_activities_data() -> Dict[str, Any]:
    """Load activities data from JSON file."""
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        else:
            print(f"Activities data file {DATA_FILE} not found.")
            return {"destinations": {}}
    except Exception as e:
        print(f"Error loading activities data: {e}")
        return {"destinations": {}}

# Load data at startup
activities_data = load_activities_data()


@mcp.tool()
async def get_destination_info(city: str) -> Dict[str, Any]:
    """
    Get comprehensive destination information including description and popular areas.
    
    Args:
        city: The city to get information for (e.g., 'san_francisco', 'new_york')
    """
    city = city.lower().replace(" ", "_")
    
    if city not in activities_data.get("destinations", {}):
        return {"error": f"Destination '{city}' not found"}
    
    destination = activities_data["destinations"][city]
    
    return {
        "name": destination.get("name", city),
        "country": destination.get("country", "Unknown"),
        "description": destination.get("description", ""),
        "popular_areas": destination.get("popular_areas", []),
        "total_indoor_activities": len(destination.get("indoor_activities", [])),
        "total_outdoor_activities": len(destination.get("outdoor_activities", []))
    }


@mcp.tool()
async def get_indoor_activities(city: str, category: str = None, duration: str = None) -> Dict[str, Any]:
    """
    Get indoor activities for a city (museums, theaters, shopping, etc.).
    
    Args:
        city: The city to get activities for
        category: Optional filter by category (culture, museum, art, entertainment)
        duration: Optional filter by duration (short, half-day, full-day, evening)
    """
    city = city.lower().replace(" ", "_")
    
    if city not in activities_data.get("destinations", {}):
        return {"error": f"City '{city}' not found"}
    
    destination = activities_data["destinations"][city]
    activities = destination.get("indoor_activities", [])
    
    # Apply filters
    if category:
        category = category.lower()
        activities = [a for a in activities if category in [c.lower() for c in a.get("categories", [])]]
    
    if duration:
        duration = duration.lower()
        activities = [a for a in activities if a.get("duration", "").lower() == duration]
    
    return {
        "city": destination.get("name", city),
        "indoor_activities": activities,
        "count": len(activities),
        "available_categories": list(set([cat for activity in destination.get("indoor_activities", []) 
                                        for cat in activity.get("categories", [])]))
    }


@mcp.tool()
async def get_outdoor_activities(city: str, category: str = None, duration: str = None) -> Dict[str, Any]:
    """
    Get outdoor activities for a city (parks, trails, sports, sightseeing).
    
    Args:
        city: The city to get activities for
        category: Optional filter by category (nature, hiking, outdoor, landmark)
        duration: Optional filter by duration (short, half-day, full-day)
    """
    city = city.lower().replace(" ", "_")
    
    if city not in activities_data.get("destinations", {}):
        return {"error": f"City '{city}' not found"}
    
    destination = activities_data["destinations"][city]
    activities = destination.get("outdoor_activities", [])
    
    # Apply filters
    if category:
        category = category.lower()
        activities = [a for a in activities if category in [c.lower() for c in a.get("categories", [])]]
    
    if duration:
        duration = duration.lower()
        activities = [a for a in activities if a.get("duration", "").lower() == duration]
    
    return {
        "city": destination.get("name", city),
        "outdoor_activities": activities,
        "count": len(activities),
        "available_categories": list(set([cat for activity in destination.get("outdoor_activities", []) 
                                        for cat in activity.get("categories", [])]))
    }


@mcp.tool()
async def get_activity_dining(city: str, activity_id: str) -> Dict[str, Any]:
    """
    Get dining recommendations near a specific activity.

    Args:
        city: The city where the activity is located
        activity_id: The ID of the activity to get dining recommendations for
    """
    city = city.lower().replace(" ", "_")
    
    if city not in activities_data.get("destinations", {}):
        return {"error": f"City '{city}' not found"}
    
    destination = activities_data["destinations"][city]
    
    # Search in both indoor and outdoor activities
    all_activities = destination.get("indoor_activities", []) + destination.get("outdoor_activities", [])
    
    activity = None
    for act in all_activities:
        if act.get("id") == activity_id:
            activity = act
            break
    
    if not activity:
        return {"error": f"Activity '{activity_id}' not found in {city}"}
    
    return {
        "activity_name": activity.get("name"),
        "activity_id": activity_id,
        "city": destination.get("name", city),
        "nearby_dining": activity.get("nearby_dining", []),
        "dining_count": len(activity.get("nearby_dining", []))
    }


@mcp.tool()
async def list_available_destinations() -> Dict[str, Any]:
    """List all available destinations in the system."""
    destinations = []
    
    for city_id, city_data in activities_data.get("destinations", {}).items():
        destinations.append({
            "id": city_id,
            "name": city_data.get("name", city_id),
            "country": city_data.get("country", "Unknown"),
            "indoor_activities_count": len(city_data.get("indoor_activities", [])),
            "outdoor_activities_count": len(city_data.get("outdoor_activities", []))
        })
    
    return {
        "destinations": destinations,
        "count": len(destinations)
    }


def main():
    """Main entry point for the activities MCP server."""
    parser = argparse.ArgumentParser(description="Activities MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default="streamable-http",
        help="Transport method to use (default: streamable-http)"
    )

    args = parser.parse_args()

    print(f"Starting activities MCP server with transport: {args.transport}")
    mcp.settings.port = int(os.getenv("MCP_PORT", "8080"))
    mcp.settings.host = '0.0.0.0'
    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()