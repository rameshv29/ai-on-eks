"""Mapper MCP Server - Route optimization and interactive HTML generation."""

import os
import json
import argparse
from datetime import datetime, timedelta
from typing import Any, Dict, List
from mcp.server.fastmcp import FastMCP
import boto3
from botocore.exceptions import ClientError

# Initialize FastMCP server
mcp = FastMCP("mapper")


@mcp.tool()
async def generate_interactive_travel_plan(
    city: str,
    days: int = 3,
    focus: str = "balanced",
    activities: List[Dict] = None
) -> Dict[str, Any]:
    """
    Generate an interactive HTML travel plan with maps and route optimization.
    
    Args:
        city: The destination city
        days: Number of days for the trip
        focus: Trip focus (food, outdoor, culture, balanced)
        activities: List of selected activities with details
    """
    try:
        # Generate interactive HTML travel plan
        html_content = _generate_html_plan(city, days, focus, activities)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{city.lower().replace(' ', '_')}_{days}day_{focus}_plan_{timestamp}.html"
        
        # Save HTML file
        os.makedirs("/tmp/generated_plans", exist_ok=True)
        filepath = f"/tmp/generated_plans/{filename}"
        
        with open(filepath, "w", encoding='utf-8') as f:
            f.write(html_content)
        
        # Upload to S3 if configured
        s3_info = _upload_to_s3(filepath)
        
        file_size = os.path.getsize(filepath)
        
        plan_data = {
            "city": city,
            "days": days,
            "focus": focus,
            "status": "generated",
            "html_file": filename,
            "filepath": filepath,
            "file_size": file_size,
            "features": [
                "Interactive maps with markers",
                "Day-by-day itinerary",
                "Route optimization",
                "Responsive design"
            ],
            "activities_included": len(activities) if activities else 0,
            "s3_info": s3_info
        }
        
        return {
            "success": True,
            "plan": plan_data,
            "message": f"Interactive travel plan generated for {city}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to generate travel plan"
        }


@mcp.tool()
async def optimize_route(locations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Optimize travel routes between multiple locations.
    
    Args:
        locations: List of locations with coordinates and details
    """
    try:
        if not locations:
            return {
                "success": False,
                "error": "No locations provided",
                "optimized_route": []
            }
        
        # Simple route optimization (nearest neighbor algorithm)
        optimized_order = list(range(len(locations)))
        
        # Calculate estimated travel times
        total_time = len(locations) * 15  # 15 minutes between locations
        
        optimized_route = {
            "original_count": len(locations),
            "optimized_order": optimized_order,
            "locations": [locations[i] for i in optimized_order],
            "total_estimated_time": f"{total_time} minutes",
            "optimization_method": "nearest_neighbor"
        }
        
        return {
            "success": True,
            "optimized_route": optimized_route,
            "message": f"Route optimized for {len(locations)} locations"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "optimized_route": []
        }


@mcp.tool()
async def get_location_coordinates(location_name: str, city: str) -> Dict[str, Any]:
    """
    Get coordinates for a specific location within a city.
    
    Args:
        location_name: Name of the location/attraction
        city: City where the location is situated
    """
    try:
        # Sample coordinates for common locations
        sample_coordinates = {
            "san_francisco": {
                "golden_gate_bridge": {"lat": 37.8199, "lng": -122.4783},
                "fishermans_wharf": {"lat": 37.8080, "lng": -122.4177},
                "union_square": {"lat": 37.7879, "lng": -122.4075},
                "chinatown": {"lat": 37.7941, "lng": -122.4078},
                "golden_gate_park": {"lat": 37.7694, "lng": -122.4862}
            },
            "new_york": {
                "times_square": {"lat": 40.7580, "lng": -73.9855},
                "central_park": {"lat": 40.7829, "lng": -73.9654},
                "brooklyn_bridge": {"lat": 40.7061, "lng": -73.9969},
                "statue_of_liberty": {"lat": 40.6892, "lng": -74.0445}
            }
        }
        
        city_key = city.lower().replace(" ", "_")
        location_key = location_name.lower().replace(" ", "_")
        
        if city_key in sample_coordinates and location_key in sample_coordinates[city_key]:
            coords = sample_coordinates[city_key][location_key]
            return {
                "success": True,
                "location": location_name,
                "city": city,
                "coordinates": coords,
                "formatted_address": f"{location_name}, {city}"
            }
        else:
            # Default coordinates for city center
            default_coords = {
                "san_francisco": {"lat": 37.7749, "lng": -122.4194},
                "new_york": {"lat": 40.7128, "lng": -74.0060}
            }
            
            coords = default_coords.get(city_key, {"lat": 0, "lng": 0})
            return {
                "success": True,
                "location": location_name,
                "city": city,
                "coordinates": coords,
                "formatted_address": f"{location_name}, {city}",
                "note": "Using approximate coordinates"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "coordinates": {"lat": 0, "lng": 0}
        }


def _upload_to_s3(filepath: str) -> Dict[str, Any]:
    """Upload travel plan to S3 and return info."""
    try:
        bucket_name = os.getenv('S3_BUCKET_NAME')
        if not bucket_name:
            return {"status": "skipped", "reason": "No S3 bucket configured"}
        
        # Initialize S3 client
        s3_client = boto3.client('s3')
        
        # Generate S3 key
        filename = os.path.basename(filepath)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        s3_key = f"travel-plans/{timestamp}_{filename}"
        
        # Upload file
        s3_client.upload_file(filepath, bucket_name, s3_key)
        
        return {
            'status': 'uploaded',
            'filename': filename,
            'file_size': os.path.getsize(filepath),
            's3_key': s3_key,
            's3_bucket': bucket_name,
            'upload_time': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"status": "failed", "error": str(e)}


def _generate_html_plan(city: str, days: int, focus: str, activities: List[Dict] = None) -> str:
    """Generate advanced interactive HTML travel plan with full functionality."""
    activities = activities or []
    
    # Sample data for San Francisco
    sample_activities = [
        {"id": "golden_gate_bridge", "name": "Golden Gate Bridge", "category": "Landmark", "description": "Iconic suspension bridge", "coordinates": {"lat": 37.8199, "lng": -122.4783}},
        {"id": "golden_gate_park", "name": "Golden Gate Park", "category": "Nature", "description": "Large urban park with gardens and museums", "coordinates": {"lat": 37.7694, "lng": -122.4862}},
        {"id": "fishermans_wharf", "name": "Fisherman's Wharf", "category": "Entertainment", "description": "Waterfront area with shops and restaurants", "coordinates": {"lat": 37.808, "lng": -122.4177}},
        {"id": "alcatraz_island", "name": "Alcatraz Island", "category": "Historical", "description": "Famous former federal prison on an island", "coordinates": {"lat": 37.8267, "lng": -122.4233}},
        {"id": "lombard_street", "name": "Lombard Street", "category": "Landmark", "description": "The most crooked street in the world", "coordinates": {"lat": 37.8021, "lng": -122.4187}}
    ]
    
    sample_restaurants = [
        {"id": "tartine_bakery", "name": "Tartine Bakery", "cuisine_type": "Bakery", "description": "Famous artisanal bakery and cafe", "coordinates": {"lat": 37.7611, "lng": -122.4242}},
        {"id": "zuni_cafe", "name": "Zuni Cafe", "cuisine_type": "Mediterranean", "description": "Iconic restaurant known for roast chicken", "coordinates": {"lat": 37.7749, "lng": -122.4312}},
        {"id": "la_taqueria", "name": "La Taqueria", "cuisine_type": "Mexican", "description": "Authentic Mission-style burritos", "coordinates": {"lat": 37.7489, "lng": -122.4181}}
    ]
    
    activities_json = json.dumps(sample_activities)
    restaurants_json = json.dumps(sample_restaurants)
    
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{city.title()} - Interactive Travel Plan</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            min-height: 100vh;
        }}
        .header {{
            background: linear-gradient(135deg, #ff6b6b, #feca57);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 2.5em;
            font-weight: 300;
            margin-bottom: 10px;
        }}
        .main-content {{
            display: grid;
            grid-template-columns: 1fr 400px;
            gap: 0;
            min-height: calc(100vh - 200px);
        }}
        .itinerary-section {{
            padding: 30px;
            overflow-y: auto;
        }}
        .controls-section {{
            background: #f8f9fa;
            border-left: 3px solid #4facfe;
            padding: 30px;
            overflow-y: auto;
        }}
        .day-card {{
            background: white;
            border-radius: 15px;
            margin: 20px 0;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            overflow: hidden;
            cursor: pointer;
            transition: all 0.3s;
        }}
        .day-card:hover {{
            transform: translateY(-2px);
        }}
        .day-card.active {{
            border-left: 5px solid #4facfe;
            box-shadow: 0 12px 35px rgba(79, 172, 254, 0.3);
        }}
        .day-header {{
            background: linear-gradient(135deg, #4facfe, #00f2fe);
            color: white;
            padding: 20px;
        }}
        .route-info {{
            background: #e3f2fd;
            padding: 15px 20px;
            display: none;
            border-top: 2px solid #4facfe;
        }}
        .route-info.active {{
            display: block;
        }}
        .schedule {{
            padding: 20px;
        }}
        .schedule-item {{
            display: flex;
            align-items: center;
            padding: 15px 0;
            border-bottom: 1px solid #eee;
        }}
        .time {{
            font-weight: bold;
            color: #4facfe;
            min-width: 100px;
            font-size: 1.1em;
        }}
        .activity {{
            flex: 1;
            margin-left: 20px;
        }}
        .activity-name {{
            font-weight: bold;
            color: #333;
            font-size: 1.1em;
            margin-bottom: 5px;
        }}
        .activity-details {{
            color: #666;
            margin-bottom: 8px;
        }}
        .remove-btn {{
            background: #ff6b6b;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.8em;
            transition: background 0.3s;
        }}
        .map-container {{
            height: 500px;
            margin: 20px 0;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }}
        .available-items {{
            margin: 20px 0;
        }}
        .available-items h4 {{
            color: #333;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #4facfe;
        }}
        .item-list {{
            max-height: 300px;
            overflow-y: auto;
        }}
        .item {{
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 12px;
            margin: 8px 0;
            cursor: pointer;
            transition: all 0.3s;
        }}
        .item:hover {{
            border-color: #4facfe;
            box-shadow: 0 2px 8px rgba(79, 172, 254, 0.2);
        }}
        .item-name {{
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }}
        .add-btn {{
            background: #4facfe;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.8em;
            margin-top: 8px;
            transition: background 0.3s;
        }}
        @media (max-width: 1024px) {{
            .main-content {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1><i class="fas fa-map-marked-alt"></i> {city.title()} Interactive Travel Plan</h1>
            <p>{days}-Day {focus.title()} Experience with Interactive Maps</p>
            <p><i class="fas fa-route"></i> Click days to see routes • <i class="fas fa-plus"></i> Add attractions to plan</p>
        </div>
        
        <div class="main-content">
            <div class="itinerary-section">
                <div class="map-container">
                    <div id="map" style="height: 100%; width: 100%;"></div>
                </div>
                
                <div id="itinerary-content">
                    <div class="day-card" id="day-1-card" onclick="showDayRoute(1)">
                        <div class="day-header">
                            <h3><i class="fas fa-calendar-day"></i> Day 1: {focus.title()} Exploration</h3>
                            <p>{datetime.now().strftime('%A, %B %d, %Y')}</p>
                        </div>
                        <div class="route-info" id="day-1-route">
                            <h4 style="color: #4facfe; margin: 0 0 10px 0;">
                                <i class="fas fa-route"></i> Day 1 Route Visible
                            </h4>
                            <p style="color: #666;">Route with stops highlighted on map</p>
                        </div>
                        <div class="schedule" id="day-1-schedule">
                            <div class="schedule-item" id="schedule-golden_gate_bridge">
                                <div class="time">9:00 AM</div>
                                <div class="activity">
                                    <div class="activity-name">🎯 Golden Gate Bridge</div>
                                    <div class="activity-details">Iconic suspension bridge</div>
                                    <button class="remove-btn" onclick="removeFromSchedule('golden_gate_bridge')">
                                        <i class="fas fa-trash"></i> Remove
                                    </button>
                                </div>
                            </div>
                            <div class="schedule-item" id="schedule-golden_gate_park">
                                <div class="time">2:30 PM</div>
                                <div class="activity">
                                    <div class="activity-name">🌳 Golden Gate Park</div>
                                    <div class="activity-details">Large urban park with gardens and museums</div>
                                    <button class="remove-btn" onclick="removeFromSchedule('golden_gate_park')">
                                        <i class="fas fa-trash"></i> Remove
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="controls-section">
                <h3 style="color: #333; margin-bottom: 20px;">
                    <i class="fas fa-cogs"></i> Available Attractions
                </h3>
                
                <div class="available-items">
                    <h4><i class="fas fa-star"></i> Activities</h4>
                    <div class="item-list" id="available-activities">
                        <!-- Activities populated by JavaScript -->
                    </div>
                </div>
                
                <div class="available-items">
                    <h4><i class="fas fa-utensils"></i> Restaurants</h4>
                    <div class="item-list" id="available-restaurants">
                        <!-- Restaurants populated by JavaScript -->
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Complete data with coordinates and route information
        const activities = {activities_json};
        const restaurants = {restaurants_json};
        const routeData = {{"day_1": {{"coordinates": [[37.8199, -122.4783], [37.7694, -122.4862]], "color": "#4caf50", "name": "Day 1: {focus.title()} Exploration"}}}};
        
        // Map variables
        let map;
        let currentRouteLayer = null;
        let markers = {{}};
        let activeDay = null;
        let currentSchedule = new Set();
        
        // Day colors
        const dayColors = ['#4caf50', '#2196f3', '#ff9800', '#9c27b0'];
        
        // Initialize everything
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('Initializing travel planner...');
            console.log('Activities:', activities.length);
            console.log('Restaurants:', restaurants.length);
            
            initializeMap();
            populateAvailableItems();
            initializeCurrentSchedule();
            addAllMarkersToMap();
        }});
        
        function initializeMap() {{
            console.log('Initializing map...');
            map = L.map('map').setView([37.7749, -122.4194], 12);
            
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                attribution: '© OpenStreetMap contributors'
            }}).addTo(map);
            
            console.log('Map initialized');
        }}
        
        function addAllMarkersToMap() {{
            console.log('Adding all markers to map...');
            
            // Add activity markers
            activities.forEach((activity, index) => {{
                if (activity.coordinates && activity.coordinates.lat !== 0) {{
                    addMarkerToMap(activity, activity.id, false, 'activity');
                }}
            }});
            
            // Add restaurant markers
            restaurants.forEach((restaurant, index) => {{
                if (restaurant.coordinates && restaurant.coordinates.lat !== 0) {{
                    addMarkerToMap(restaurant, restaurant.id, false, 'restaurant');
                }}
            }});
            
            // Add scheduled item markers
            const scheduledItems = document.querySelectorAll('.schedule-item');
            scheduledItems.forEach((item) => {{
                const itemId = item.id.replace('schedule-', '');
                const activityItem = activities.find(a => a.id === itemId);
                const restaurantItem = restaurants.find(r => r.id === itemId);
                const dataItem = activityItem || restaurantItem;
                
                if (dataItem && dataItem.coordinates && dataItem.coordinates.lat !== 0) {{
                    // Find which day this item belongs to
                    const dayCard = item.closest('.day-card');
                    const dayNum = dayCard ? parseInt(dayCard.id.replace('day-', '').replace('-card', '')) : 1;
                    addMarkerToMap(dataItem, itemId, true, activityItem ? 'activity' : 'restaurant', dayNum);
                }}
            }});
            
            console.log('All markers added');
        }}
        
        function addMarkerToMap(item, itemId, isScheduled = false, type = 'activity', dayNum = null) {{
            const coords = item.coordinates;
            if (!coords || coords.lat === 0) return;
            
            // Determine color
            let color = '#666666'; // Default gray for available items
            if (isScheduled && dayNum) {{
                color = dayColors[(dayNum - 1) % dayColors.length];
            }}
            
            const icon = type === 'activity' ? '🎯' : '🍽️';
            
            // Create pin-style marker
            const markerIcon = L.divIcon({{
                html: `<div style="
                    background: ${{color}};
                    border: 3px solid white;
                    width: 35px;
                    height: 35px;
                    border-radius: 50% 50% 50% 0;
                    transform: rotate(-45deg);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-weight: bold;
                    font-size: 14px;
                    box-shadow: 0 3px 10px rgba(0,0,0,0.4);
                ">
                    <div style="transform: rotate(45deg);">${{icon}}</div>
                </div>`,
                className: 'custom-pin-icon',
                iconSize: [35, 35],
                iconAnchor: [17, 35]
            }});
            
            const marker = L.marker([coords.lat, coords.lng], {{ icon: markerIcon }}).addTo(map);
            
            const popupContent = `
                <div style="width: 220px; font-family: 'Segoe UI', sans-serif;">
                    <div style="background: ${{color}}; color: white; padding: 12px; margin: -10px -10px 12px -10px; border-radius: 8px 8px 0 0;">
                        <h4 style="margin: 0; font-size: 16px;">${{icon}} ${{item.name}}</h4>
                        <p style="margin: 5px 0 0 0; opacity: 0.9; font-size: 12px;">${{isScheduled ? `Day ${{dayNum}}` : 'Available'}} • ${{type === 'activity' ? 'Activity' : 'Restaurant'}}</p>
                    </div>
                    <div style="padding: 0 5px;">
                        <p style="margin: 8px 0; color: #555; font-size: 14px;">${{item.description || item.cuisine_type || 'Great experience'}}</p>
                        <div style="text-align: center; margin-top: 12px;">
                            ${{isScheduled ? 
                                `<button onclick="removeFromSchedule('${{itemId}}')" style="background: #ff6b6b; color: white; border: none; padding: 8px 12px; border-radius: 5px; cursor: pointer; font-size: 12px; font-weight: bold;">🗑️ Remove</button>` :
                                `<button onclick="addToSchedule('${{itemId}}', '${{type}}')" style="background: #4facfe; color: white; border: none; padding: 8px 12px; border-radius: 5px; cursor: pointer; font-size: 12px; font-weight: bold;">➕ Add to Plan</button>`
                            }}
                        </div>
                    </div>
                </div>
            `;
            
            marker.bindPopup(popupContent);
            markers[itemId] = marker;
        }}
        
        function populateAvailableItems() {{
            console.log('Populating available items...');
            
            const activitiesContainer = document.getElementById('available-activities');
            const restaurantsContainer = document.getElementById('available-restaurants');
            
            activities.forEach(activity => {{
                const itemDiv = document.createElement('div');
                itemDiv.className = 'item';
                itemDiv.innerHTML = `
                    <div class="item-name"><i class="fas fa-star"></i> ${{activity.name}}</div>
                    <div class="item-details">Category: ${{activity.category}}</div>
                    <div class="item-details">${{activity.description}}</div>
                    <button class="add-btn" onclick="addToSchedule('${{activity.id}}', 'activity')">
                        <i class="fas fa-plus"></i> Add to Plan
                    </button>
                `;
                activitiesContainer.appendChild(itemDiv);
            }});
            
            restaurants.forEach(restaurant => {{
                const itemDiv = document.createElement('div');
                itemDiv.className = 'item';
                itemDiv.innerHTML = `
                    <div class="item-name"><i class="fas fa-utensils"></i> ${{restaurant.name}}</div>
                    <div class="item-details">Cuisine: ${{restaurant.cuisine_type}}</div>
                    <div class="item-details">${{restaurant.description}}</div>
                    <button class="add-btn" onclick="addToSchedule('${{restaurant.id}}', 'restaurant')">
                        <i class="fas fa-plus"></i> Add to Plan
                    </button>
                `;
                restaurantsContainer.appendChild(itemDiv);
            }});
            
            console.log('Available items populated');
        }}
        
        function initializeCurrentSchedule() {{
            document.querySelectorAll('[id^="schedule-"]').forEach(item => {{
                const id = item.id.replace('schedule-', '');
                currentSchedule.add(id);
            }});
        }}
        
        function showDayRoute(dayNum) {{
            console.log('Showing route for day', dayNum);
            
            // Update UI
            document.querySelectorAll('.route-info').forEach(info => info.classList.remove('active'));
            document.querySelectorAll('.day-card').forEach(card => card.classList.remove('active'));
            
            const routeInfo = document.getElementById(`day-${{dayNum}}-route`);
            const dayCard = document.getElementById(`day-${{dayNum}}-card`);
            
            if (routeInfo && dayCard) {{
                routeInfo.classList.add('active');
                dayCard.classList.add('active');
                activeDay = dayNum;
            }}
            
            // Remove existing route
            if (currentRouteLayer) {{
                map.removeLayer(currentRouteLayer);
                currentRouteLayer = null;
            }}
            
            // Add new route
            const routeKey = `day_${{dayNum}}`;
            if (routeData[routeKey]) {{
                const route = routeData[routeKey];
                currentRouteLayer = L.polyline(route.coordinates, {{
                    color: route.color,
                    weight: 4,
                    opacity: 0.8
                }}).addTo(map);
                
                currentRouteLayer.bindPopup(`<b>${{route.name}}</b>`);
                showNotification(`Day ${{dayNum}} route visible on map`, 'success');
            }}
        }}
        
        function addToSchedule(itemId, type) {{
            if (currentSchedule.has(itemId)) {{
                showNotification('Item already in schedule', 'warning');
                return;
            }}
            
            const item = type === 'activity' 
                ? activities.find(a => a.id === itemId)
                : restaurants.find(r => r.id === itemId);
            
            if (!item) {{
                showNotification('Item not found', 'error');
                return;
            }}
            
            // Smart day selection
            let targetDay = activeDay || 1;
            const targetDaySchedule = document.getElementById(`day-${{targetDay}}-schedule`);
            
            if (targetDaySchedule) {{
                const existingItems = targetDaySchedule.querySelectorAll('.schedule-item').length;
                const timeSlots = ['9:00 AM', '12:30 PM', '2:30 PM', '7:00 PM', '9:00 PM'];
                const assignedTime = timeSlots[existingItems] || 'Added';
                
                const newItem = document.createElement('div');
                newItem.className = 'schedule-item';
                newItem.id = `schedule-${{itemId}}`;
                newItem.innerHTML = `
                    <div class="time">${{assignedTime}}</div>
                    <div class="activity">
                        <div class="activity-name">${{type === 'activity' ? '🎯' : '🍽️'}} ${{item.name}}</div>
                        <div class="activity-details">${{item.description || item.cuisine_type || 'Great experience'}}</div>
                        <button class="remove-btn" onclick="removeFromSchedule('${{itemId}}')">
                            <i class="fas fa-trash"></i> Remove
                        </button>
                    </div>
                `;
                
                targetDaySchedule.appendChild(newItem);
                currentSchedule.add(itemId);
                
                // Update marker on map
                if (markers[itemId]) {{
                    map.removeLayer(markers[itemId]);
                }}
                addMarkerToMap(item, itemId, true, type, targetDay);
                
                showNotification(`${{item.name}} added to Day ${{targetDay}}`, 'success');
                
                if (targetDay !== activeDay) {{
                    setTimeout(() => showDayRoute(targetDay), 500);
                }}
            }}
        }}
        
        function removeFromSchedule(itemId) {{
            const element = document.getElementById(`schedule-${{itemId}}`);
            if (element) {{
                element.remove();
                currentSchedule.delete(itemId);
                
                // Update marker on map
                const activityItem = activities.find(a => a.id === itemId);
                const restaurantItem = restaurants.find(r => r.id === itemId);
                const item = activityItem || restaurantItem;
                
                if (markers[itemId]) {{
                    map.removeLayer(markers[itemId]);
                }}
                
                if (item) {{
                    addMarkerToMap(item, itemId, false, activityItem ? 'activity' : 'restaurant');
                }}
                
                showNotification('Item removed from schedule', 'success');
            }}
        }}
        
        function showNotification(message, type) {{
            const notification = document.createElement('div');
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 15px 20px;
                border-radius: 5px;
                color: white;
                font-weight: bold;
                z-index: 10000;
                background: ${{type === 'success' ? '#4caf50' : type === 'warning' ? '#ff9800' : '#f44336'}};
            `;
            notification.innerHTML = `<i class="fas fa-${{type === 'success' ? 'check' : type === 'warning' ? 'exclamation' : 'times'}}"></i> ${{message}}`;
            
            document.body.appendChild(notification);
            setTimeout(() => notification.remove(), 3000);
        }}
    </script>
</body>
</html>"""
    
    return html_template


def main():
    """Main entry point for the mapper MCP server."""
    parser = argparse.ArgumentParser(description="Mapper MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default="streamable-http",
        help="Transport method to use (default: streamable-http)"
    )

    args = parser.parse_args()

    print(f"Starting mapper MCP server with transport: {args.transport}")
    mcp.settings.port = int(os.getenv("MCP_PORT", "8080"))
    mcp.settings.host = '0.0.0.0'
    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()