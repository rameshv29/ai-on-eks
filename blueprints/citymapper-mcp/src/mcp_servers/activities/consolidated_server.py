#!/usr/bin/env python3
"""
Consolidated Activities MCP Server
Handles destinations, indoor/outdoor activities, and activity-tied dining
Consolidates functionality from Travel + Activities + minimal Food servers
"""
import os
import sys
import json
import logging
from typing import Dict, List, Any, Optional
from mcp.server import FastMCP
from fastapi import Response

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create the consolidated Activities MCP server
mcp = FastMCP(
    name="Consolidated Activities Server",
    host="0.0.0.0",
    port=8004
)

# Health check endpoint
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    """Health check endpoint for load balancer"""
    try:
        # Test data loading
        load_activities_data()
        return Response(
            content="healthy",
            status_code=200,
            media_type="text/plain"
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return Response(
            content=f"unhealthy - {str(e)}",
            status_code=503,
            media_type="text/plain"
        )

# Data loading functions
DATA_FILE = os.path.join(os.path.dirname(__file__), "consolidated_activities_data.json")

def load_activities_data() -> Dict[str, Any]:
    """Load consolidated activities data from JSON file"""
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        else:
            logger.warning(f"Activities data file {DATA_FILE} not found.")
            return {"destinations": {}}
    except Exception as e:
        logger.error(f"Error loading activities data: {e}")
        return {"destinations": {}}

# Load data at startup
activities_data = load_activities_data()

# MCP Tools - Consolidated functionality
@mcp.tool()
def get_destination_info(city: str) -> Dict[str, Any]:
    """
    Get comprehensive destination information including description, popular areas.
    
    Parameters:
    - city: The city to get information for (e.g., 'san_francisco', 'new_york')
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
def get_indoor_activities(city: str, category: str = None, duration: str = None) -> Dict[str, Any]:
    """
    Get indoor activities for a city (museums, theaters, shopping, etc.).
    
    Parameters:
    - city: The city to get activities for
    - category: Optional filter by category (culture, museum, art, entertainment)
    - duration: Optional filter by duration (short, half-day, full-day, evening)
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
def get_outdoor_activities(city: str, category: str = None, duration: str = None) -> Dict[str, Any]:
    """
    Get outdoor activities for a city (parks, trails, sports, sightseeing).
    
    Parameters:
    - city: The city to get activities for
    - category: Optional filter by category (nature, hiking, outdoor, landmark)
    - duration: Optional filter by duration (short, half-day, full-day)
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
def get_activity_dining(city: str, activity_id: str) -> Dict[str, Any]:
    """
    Get dining recommendations near a specific activity.
    
    Parameters:
    - city: The city where the activity is located
    - activity_id: The ID of the activity to get dining recommendations for
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
def get_popular_areas(city: str) -> Dict[str, Any]:
    """
    Get popular areas/districts in a city.
    
    Parameters:
    - city: The city to get popular areas for
    """
    city = city.lower().replace(" ", "_")
    
    if city not in activities_data.get("destinations", {}):
        return {"error": f"City '{city}' not found"}
    
    destination = activities_data["destinations"][city]
    
    return {
        "city": destination.get("name", city),
        "popular_areas": destination.get("popular_areas", []),
        "count": len(destination.get("popular_areas", []))
    }

@mcp.tool()
def list_available_destinations() -> Dict[str, Any]:
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

@mcp.tool()
def get_all_activities(city: str, activity_type: str = None) -> Dict[str, Any]:
    """
    Get all activities (both indoor and outdoor) for a city.
    
    Parameters:
    - city: The city to get activities for
    - activity_type: Optional filter ('indoor', 'outdoor', or None for both)
    """
    city = city.lower().replace(" ", "_")
    
    if city not in activities_data.get("destinations", {}):
        return {"error": f"City '{city}' not found"}
    
    destination = activities_data["destinations"][city]
    
    indoor_activities = destination.get("indoor_activities", [])
    outdoor_activities = destination.get("outdoor_activities", [])
    
    if activity_type == "indoor":
        activities = indoor_activities
    elif activity_type == "outdoor":
        activities = outdoor_activities
    else:
        # Combine both with type indicator
        activities = []
        for activity in indoor_activities:
            activity_copy = activity.copy()
            activity_copy["activity_type"] = "indoor"
            activities.append(activity_copy)
        for activity in outdoor_activities:
            activity_copy = activity.copy()
            activity_copy["activity_type"] = "outdoor"
            activities.append(activity_copy)
    
    return {
        "city": destination.get("name", city),
        "activities": activities,
        "count": len(activities),
        "indoor_count": len(indoor_activities),
        "outdoor_count": len(outdoor_activities)
    }

if __name__ == "__main__":
    logger.info("🎯 Starting Consolidated Activities MCP Server...")
    logger.info("📍 Handles destinations, indoor/outdoor activities, and dining")
    logger.info(f"📊 Loaded {len(activities_data.get('destinations', {}))} destinations")
    logger.info("🌐 Available endpoints: /health")
    
    # Start the server using FastMCP with streamable-http transport
    mcp.run(transport="streamable-http")
