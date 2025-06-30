# travel/server.py
from mcp.server import FastMCP
import json
import os
from typing import List, Dict, Any, Optional
import logging
from fastapi import Response

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create the Travel MCP server
mcp = FastMCP(
    name="Travel Information Server",
    host="0.0.0.0",
    port=8001
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

# Path to the travel data file
DATA_FILE = os.path.join(os.path.dirname(__file__), "travel_data.json")

class TravelRetriever:
    """Agentic RAG system for retrieving and managing travel destination data."""
    
    def __init__(self, data_file: str):
        self.data_file = data_file
        self.data = self._load_data()
        
    def _load_data(self) -> Dict[str, Any]:
        """Load data from the JSON file."""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            else:
                logger.warning(f"Data file {self.data_file} not found. Creating empty data structure.")
                return {"destinations": {}}
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return {"destinations": {}}
    
    def _save_data(self) -> None:
        """Save data to the JSON file."""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving data: {e}")
    
    def get_destination_data(self, destination: str) -> Optional[Dict[str, Any]]:
        """Get all data for a specific destination."""
        destination = destination.lower()
        return self.data.get("destinations", {}).get(destination)
    
    def get_all_destinations(self) -> List[str]:
        """Get a list of all available destinations."""
        return list(self.data.get("destinations", {}).keys())
    
    def get_accommodations(self, destination: str) -> List[Dict[str, Any]]:
        """Get accommodations for a destination."""
        destination_data = self.get_destination_data(destination)
        if destination_data:
            return destination_data.get("accommodations", [])
        return []
    
    def get_popular_areas(self, destination: str) -> List[str]:
        """Get popular areas for a destination."""
        destination_data = self.get_destination_data(destination)
        if destination_data:
            return destination_data.get("popular_areas", [])
        return []
    
    def add_destination(self, destination: str, data: Dict[str, Any]) -> bool:
        """Add a new destination to the database."""
        destination = destination.lower()
        if "destinations" not in self.data:
            self.data["destinations"] = {}
        
        self.data["destinations"][destination] = data
        self._save_data()
        return True

# Initialize the travel retriever
travel_retriever = TravelRetriever(DATA_FILE)

@mcp.tool()
def get_destination_info(destination: str) -> dict:
    """Get information about a travel destination."""
    destination = destination.lower()
    
    destination_data = travel_retriever.get_destination_data(destination)
    if not destination_data:
        return {
            "error": f"Destination '{destination}' not found",
            "available_destinations": travel_retriever.get_all_destinations()
        }
    
    return destination_data

@mcp.tool()
def list_accommodations(destination: str) -> dict:
    """List available accommodations for a destination."""
    destination = destination.lower()
    
    accommodations = travel_retriever.get_accommodations(destination)
    if not accommodations:
        if not travel_retriever.get_destination_data(destination):
            return {
                "error": f"Destination '{destination}' not found",
                "available_destinations": travel_retriever.get_all_destinations()
            }
        else:
            return {
                "error": f"No accommodations found for '{destination}'",
                "suggestion": "Try a different destination"
            }
    
    return {"accommodations": accommodations}

@mcp.tool()
def get_popular_areas(destination: str) -> dict:
    """Get popular areas to visit in a destination."""
    destination = destination.lower()
    
    areas = travel_retriever.get_popular_areas(destination)
    if not areas:
        if not travel_retriever.get_destination_data(destination):
            return {
                "error": f"Destination '{destination}' not found",
                "available_destinations": travel_retriever.get_all_destinations()
            }
        else:
            return {
                "error": f"No popular areas found for '{destination}'",
                "suggestion": "Try a different destination"
            }
    
    return {"popular_areas": areas}

@mcp.tool()
def list_available_destinations() -> dict:
    """List all available destinations in the database."""
    destinations = travel_retriever.get_all_destinations()
    return {
        "destinations": destinations,
        "count": len(destinations)
    }

@mcp.tool()
def get_accommodation_by_type(destination: str, accommodation_type: str) -> dict:
    """Get accommodations of a specific type for a destination."""
    destination = destination.lower()
    accommodation_type = accommodation_type.lower()
    
    accommodations = travel_retriever.get_accommodations(destination)
    if not accommodations:
        if not travel_retriever.get_destination_data(destination):
            return {
                "error": f"Destination '{destination}' not found",
                "available_destinations": travel_retriever.get_all_destinations()
            }
        else:
            return {
                "error": f"No accommodations found for '{destination}'",
                "suggestion": "Try a different destination"
            }
    
    filtered_accommodations = [a for a in accommodations if a.get("type", "").lower() == accommodation_type]
    
    if not filtered_accommodations:
        return {
            "error": f"No {accommodation_type} accommodations found for '{destination}'",
            "available_types": list(set(a.get("type", "") for a in accommodations))
        }
    
    return {
        "accommodations": filtered_accommodations,
        "count": len(filtered_accommodations)
    }

# Start the MCP server
if __name__ == "__main__":
    logger.info(f"Starting Travel Server with {len(travel_retriever.get_all_destinations())} destinations")
    mcp.run(transport="streamable-http")
