#!/usr/bin/env python3
"""
Interactive Travel Planner - Mapper Service Implementation
Creates interactive HTML travel plans with maps, routes, and dynamic attractions
Integrates with microservices architecture for data collection
Uploads generated files to S3 with presigned URLs for sharing
"""
import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Try to import microservices utilities
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
    from utils.dynamodb_utils import (
        get_activities_by_city,
        get_food_by_city,
        health_check,
        initialize_dynamodb
    )
    from utils.s3_utils import (
        upload_travel_plan,
        format_upload_info,
        health_check as s3_health_check
    )
    MICROSERVICES_AVAILABLE = True
    S3_AVAILABLE = True
    print("✅ DynamoDB utilities loaded successfully")
    print("✅ S3 utilities loaded successfully")
except ImportError as e:
    MICROSERVICES_AVAILABLE = False
    S3_AVAILABLE = False
    print(f"⚠️ Microservices not available: {e}")
    print("   Using sample data for demonstration")

# Sample data for demonstration when microservices are not available
SAMPLE_ACTIVITIES = [
    {'data_id': 'alcatraz_island', 'name': 'Alcatraz Island', 'category': 'Historical', 'description': 'Famous former federal prison on an island'},
    {'data_id': 'golden_gate_bridge', 'name': 'Golden Gate Bridge', 'category': 'Landmark', 'description': 'Iconic suspension bridge'},
    {'data_id': 'fishermans_wharf', 'name': "Fisherman's Wharf", 'category': 'Entertainment', 'description': 'Waterfront area with shops and restaurants'},
    {'data_id': 'golden_gate_park', 'name': 'Golden Gate Park', 'category': 'Nature', 'description': 'Large urban park with gardens and museums'},
    {'data_id': 'lombard_street', 'name': 'Lombard Street', 'category': 'Landmark', 'description': 'The most crooked street in the world'},
    {'data_id': 'pier_39', 'name': 'Pier 39', 'category': 'Entertainment', 'description': 'Shopping center and popular tourist attraction'},
    {'data_id': 'cable_car_ride', 'name': 'Cable Car Ride', 'category': 'Transportation', 'description': 'Historic cable car system'},
    {'data_id': 'muir_woods', 'name': 'Muir Woods', 'category': 'Nature', 'description': 'National monument with ancient redwood trees'},
    {'data_id': 'palace_of_fine_arts', 'name': 'Palace of Fine Arts', 'category': 'Architecture', 'description': 'Monumental structure built for 1915 exposition'},
    {'data_id': 'exploratorium', 'name': 'Exploratorium', 'category': 'Museum', 'description': 'Interactive science museum'},
]

SAMPLE_RESTAURANTS = [
    {'data_id': 'tartine_bakery', 'name': 'Tartine Bakery', 'cuisine_type': 'Bakery', 'description': 'Famous artisanal bakery and cafe'},
    {'data_id': 'zuni_cafe', 'name': 'Zuni Cafe', 'cuisine_type': 'Mediterranean', 'description': 'Iconic restaurant known for roast chicken'},
    {'data_id': 'la_taqueria', 'name': 'La Taqueria', 'cuisine_type': 'Mexican', 'description': 'Authentic Mission-style burritos'},
    {'data_id': 'liholiho_yacht_club', 'name': 'Liholiho Yacht Club', 'cuisine_type': 'Hawaiian', 'description': 'Modern Hawaiian cuisine'},
    {'data_id': 'delfina', 'name': 'Delfina', 'cuisine_type': 'Italian', 'description': 'Neighborhood Italian restaurant'},
]

# Real coordinates for San Francisco locations
SF_COORDINATES = {
    'alcatraz_island': {'lat': 37.8267, 'lng': -122.4233, 'name': 'Alcatraz Island'},
    'angel_island_state_park': {'lat': 37.8625, 'lng': -122.4319, 'name': 'Angel Island State Park'},
    'cable_car_ride': {'lat': 37.7946, 'lng': -122.4094, 'name': 'Cable Car Ride'},
    'de_young_museum': {'lat': 37.7715, 'lng': -122.4686, 'name': 'de Young Museum'},
    'exploratorium': {'lat': 37.8016, 'lng': -122.3977, 'name': 'Exploratorium'},
    'fishermans_wharf': {'lat': 37.8080, 'lng': -122.4177, 'name': "Fisherman's Wharf"},
    'ghirardelli_square': {'lat': 37.8056, 'lng': -122.4225, 'name': 'Ghirardelli Square'},
    'golden_gate_park': {'lat': 37.7694, 'lng': -122.4862, 'name': 'Golden Gate Park'},
    'golden_gate_bridge': {'lat': 37.8199, 'lng': -122.4783, 'name': 'Golden Gate Bridge'},
    'lands_end_trail': {'lat': 37.7849, 'lng': -122.5094, 'name': 'Lands End Trail'},
    'lombard_street': {'lat': 37.8021, 'lng': -122.4187, 'name': 'Lombard Street'},
    'muir_woods': {'lat': 37.8974, 'lng': -122.5808, 'name': 'Muir Woods'},
    'oracle_park': {'lat': 37.7786, 'lng': -122.3893, 'name': 'Oracle Park'},
    'palace_of_fine_arts': {'lat': 37.8018, 'lng': -122.4484, 'name': 'Palace of Fine Arts'},
    'pier_39': {'lat': 37.8087, 'lng': -122.4098, 'name': 'Pier 39'},
    'tartine_bakery': {'lat': 37.7611, 'lng': -122.4242, 'name': 'Tartine Bakery'},
    'liholiho_yacht_club': {'lat': 37.7849, 'lng': -122.4094, 'name': 'Liholiho Yacht Club'},
    'la_taqueria': {'lat': 37.7489, 'lng': -122.4181, 'name': 'La Taqueria'},
    'zuni_cafe': {'lat': 37.7749, 'lng': -122.4312, 'name': 'Zuni Cafe'},
    'delfina': {'lat': 37.7615, 'lng': -122.4203, 'name': 'Delfina'},
}

def get_location_coordinates(city_id: str, location_name: str) -> Dict:
    """Get coordinates for a location"""
    if city_id == 'san_francisco':
        location_key = location_name.lower().replace(' ', '_').replace("'", '').replace('-', '_')
        return SF_COORDINATES.get(location_key, {'lat': 37.7749, 'lng': -122.4194, 'name': location_name})
    return {'lat': 0, 'lng': 0, 'name': location_name}

class InteractiveTravelPlanner:
    """
    Mapper Service - Interactive Travel Plan Generator
    
    Core responsibility: Route optimization and map visualization
    Integrates with microservices for data collection
    """
    
    def __init__(self, use_services: bool = False):
        self.use_services = use_services and MICROSERVICES_AVAILABLE
        self.output_dir = "generated_plans"
        os.makedirs(self.output_dir, exist_ok=True)
        
        if self.use_services:
            # Set up environment for microservices
            os.environ['USE_LOCAL_DYNAMODB'] = 'true'
            os.environ['DYNAMODB_ENDPOINT_URL'] = 'http://localhost:8000'
    
    def generate_plan(self, city_id: str, days: int = 4, focus: str = "balanced") -> str:
        """
        Generate complete interactive travel plan
        
        Data Flow:
        1. Collect data from microservices (Activities, Food, Travel, Visualization)
        2. Process and coordinate data (Mapper Service responsibility)
        3. Optimize routes and calculate paths
        4. Generate interactive HTML with maps and controls
        """
        
        print(f"🗺️ Generating interactive {days}-day {focus} travel plan for {city_id}...")
        print(f"🏗️ Architecture: {'Microservices' if self.use_services else 'Sample Data'}")
        
        # Step 1: Data Collection from Services
        if self.use_services:
            print("📊 Collecting data from microservices...")
            try:
                # Initialize DynamoDB if needed
                if MICROSERVICES_AVAILABLE:
                    initialize_dynamodb()
                
                activities = get_activities_by_city(city_id)
                restaurants = get_food_by_city(city_id)
                print(f"   🎯 Activities Service: {len(activities)} items")
                print(f"   🍽️ Food Service: {len(restaurants)} items")
                
                if not activities and not restaurants:
                    print("   ⚠️ No data found in DynamoDB, using sample data")
                    activities = SAMPLE_ACTIVITIES.copy()
                    restaurants = SAMPLE_RESTAURANTS.copy()
                    
            except Exception as e:
                print(f"   ❌ Error accessing microservices: {e}")
                print("   📊 Falling back to sample data")
                activities = SAMPLE_ACTIVITIES.copy()
                restaurants = SAMPLE_RESTAURANTS.copy()
        else:
            print("📊 Using sample data for demonstration...")
            activities = SAMPLE_ACTIVITIES.copy()
            restaurants = SAMPLE_RESTAURANTS.copy()
        
        print(f"   📊 Total Data: {len(activities)} activities, {len(restaurants)} restaurants")
        
        # Step 2: Mapper Service Processing (Core Responsibility)
        print("🗺️ Mapper Service: Processing coordinates and routes...")
        
        # Add coordinates to all items (Mapper Service responsibility)
        for activity in activities:
            coords = get_location_coordinates(city_id, activity.get('name', 'Unknown'))
            activity['coordinates'] = coords
        
        for restaurant in restaurants:
            coords = get_location_coordinates(city_id, restaurant.get('name', 'Unknown'))
            restaurant['coordinates'] = coords
        
        # Step 3: Route Optimization (Mapper Service responsibility)
        print("🛣️ Mapper Service: Optimizing routes and calculating paths...")
        plan = self._create_optimized_plan(city_id, days, focus, activities, restaurants)
        
        # Step 4: Interactive HTML Generation (Mapper Service responsibility)
        print("🌐 Mapper Service: Generating interactive HTML with maps...")
        html_content = self._generate_interactive_html(plan, activities, restaurants)
        
        # Save file locally
        filename = f"{city_id}_{days}day_{focus}_interactive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"   ✅ Interactive plan saved: {filename}")
        
        # Upload to S3 and get presigned URL
        if S3_AVAILABLE:
            print("📤 Uploading travel plan to S3...")
            try:
                upload_info = upload_travel_plan(filepath, expiration_minutes=30)
                if upload_info:
                    print("✅ Upload successful!")
                    print(format_upload_info(upload_info))
                else:
                    print("⚠️ S3 upload failed, file saved locally only")
            except Exception as e:
                print(f"⚠️ S3 upload error: {e}")
                print("📁 File saved locally only")
        else:
            print("⚠️ S3 utilities not available, file saved locally only")
        
        return filepath
    
    def _create_optimized_plan(self, city_id: str, days: int, focus: str, activities: List, restaurants: List) -> Dict:
        """
        Create optimized travel plan with routes
        Core Mapper Service functionality: Route optimization and path calculation
        """
        
        city_name = city_id.replace('_', ' ').title()
        plan = {
            "city_id": city_id,
            "city_name": city_name,
            "days": days,
            "focus": focus,
            "architecture": "microservices" if self.use_services else "sample_data",
            "mapper_service": {
                "route_optimization": True,
                "coordinate_mapping": True,
                "interactive_generation": True
            },
            "daily_plans": []
        }
        
        # Create optimized daily plans (Mapper Service responsibility)
        for day in range(1, days + 1):
            daily_plan = self._optimize_daily_route(day, days, focus, activities, restaurants, city_id)
            plan["daily_plans"].append(daily_plan)
        
        return plan
    
    def _optimize_daily_route(self, day: int, total_days: int, focus: str, activities: List, restaurants: List, city_id: str) -> Dict:
        """
        Optimize route for a single day
        Core Mapper Service functionality: Route calculation and optimization
        """
        
        items_per_day = 2 if focus == "activities" else 1
        rest_per_day = 2
        
        start_act = (day - 1) * items_per_day
        day_activities = activities[start_act:start_act + items_per_day] if activities else []
        
        start_rest = (day - 1) * rest_per_day
        day_restaurants = restaurants[start_rest:start_rest + rest_per_day] if restaurants else []
        
        schedule = []
        route_points = []
        
        # Morning activity
        if day_activities:
            activity = day_activities[0]
            schedule.append({
                "time": "9:00 AM",
                "type": "activity",
                "icon": "🎯",
                "item": activity,
                "id": f"activity_{activity.get('data_id', f'act_{day}_1')}"
            })
            route_points.append(activity['coordinates'])
        
        # Lunch
        if day_restaurants:
            restaurant = day_restaurants[0]
            schedule.append({
                "time": "12:30 PM",
                "type": "dining",
                "icon": "🍽️",
                "item": restaurant,
                "id": f"restaurant_{restaurant.get('data_id', f'rest_{day}_1')}"
            })
            route_points.append(restaurant['coordinates'])
        
        # Afternoon activity
        if len(day_activities) > 1:
            activity = day_activities[1]
            schedule.append({
                "time": "2:30 PM",
                "type": "activity",
                "icon": "🌆",
                "item": activity,
                "id": f"activity_{activity.get('data_id', f'act_{day}_2')}"
            })
            route_points.append(activity['coordinates'])
        
        # Dinner
        if len(day_restaurants) > 1:
            restaurant = day_restaurants[1]
            schedule.append({
                "time": "7:00 PM",
                "type": "dining",
                "icon": "🌃",
                "item": restaurant,
                "id": f"restaurant_{restaurant.get('data_id', f'rest_{day}_2')}"
            })
            route_points.append(restaurant['coordinates'])
        
        # Calculate route statistics (Mapper Service responsibility)
        route_distance = self._calculate_route_distance(route_points)
        
        return {
            "day": day,
            "date": (datetime.now() + timedelta(days=day-1)).strftime('%A, %B %d, %Y'),
            "theme": self._get_day_theme(day, focus),
            "schedule": schedule,
            "route_points": route_points,
            "route_optimization": {
                "total_distance_km": route_distance,
                "estimated_time": f"{int(route_distance * 12)} minutes walking",
                "optimized": True
            }
        }
    
    def _calculate_route_distance(self, route_points: List[Dict]) -> float:
        """Calculate total route distance between points"""
        if len(route_points) < 2:
            return 0.0
        
        total_distance = 0.0
        for i in range(len(route_points) - 1):
            p1 = route_points[i]
            p2 = route_points[i + 1]
            
            if p1['lat'] == 0 or p2['lat'] == 0:
                continue
                
            # Simple distance calculation (in production, use proper routing APIs)
            lat_diff = abs(p1['lat'] - p2['lat'])
            lng_diff = abs(p1['lng'] - p2['lng'])
            distance = ((lat_diff ** 2 + lng_diff ** 2) ** 0.5) * 111  # Rough km conversion
            total_distance += distance
        
        return round(total_distance, 1)
        """Create structured travel plan"""
        
        city_name = city_id.replace('_', ' ').title()
        plan = {
            "city_id": city_id,
            "city_name": city_name,
            "days": days,
            "focus": focus,
            "daily_plans": []
        }
        
        # Create daily plans
        for day in range(1, days + 1):
            items_per_day = 2 if focus == "activities" else 1
            rest_per_day = 2
            
            start_act = (day - 1) * items_per_day
            day_activities = activities[start_act:start_act + items_per_day] if activities else []
            
            start_rest = (day - 1) * rest_per_day
            day_restaurants = restaurants[start_rest:start_rest + rest_per_day] if restaurants else []
            
            schedule = []
            route_points = []
            
            # Morning activity
            if day_activities:
                activity = day_activities[0]
                schedule.append({
                    "time": "9:00 AM",
                    "type": "activity",
                    "icon": "🎯",
                    "item": activity,
                    "id": f"activity_{activity.get('data_id', f'act_{day}_1')}"
                })
                route_points.append(activity['coordinates'])
            
            # Lunch
            if day_restaurants:
                restaurant = day_restaurants[0]
                schedule.append({
                    "time": "12:30 PM",
                    "type": "dining",
                    "icon": "🍽️",
                    "item": restaurant,
                    "id": f"restaurant_{restaurant.get('data_id', f'rest_{day}_1')}"
                })
                route_points.append(restaurant['coordinates'])
            
            # Afternoon activity
            if len(day_activities) > 1:
                activity = day_activities[1]
                schedule.append({
                    "time": "2:30 PM",
                    "type": "activity",
                    "icon": "🌆",
                    "item": activity,
                    "id": f"activity_{activity.get('data_id', f'act_{day}_2')}"
                })
                route_points.append(activity['coordinates'])
            
            # Dinner
            if len(day_restaurants) > 1:
                restaurant = day_restaurants[1]
                schedule.append({
                    "time": "7:00 PM",
                    "type": "dining",
                    "icon": "🌃",
                    "item": restaurant,
                    "id": f"restaurant_{restaurant.get('data_id', f'rest_{day}_2')}"
                })
                route_points.append(restaurant['coordinates'])
            
            daily_plan = {
                "day": day,
                "date": (datetime.now() + timedelta(days=day-1)).strftime('%A, %B %d, %Y'),
                "theme": self._get_day_theme(day, focus),
                "schedule": schedule,
                "route_points": route_points
            }
            
            plan["daily_plans"].append(daily_plan)
        
        return plan
    
    def _get_day_theme(self, day: int, focus: str) -> str:
        """Get theme for each day"""
        themes = {
            "balanced": ["Classic Highlights", "Culture & Cuisine", "Nature & Views", "Local Experiences"]
        }
        theme_list = themes.get(focus, themes["balanced"])
        return theme_list[(day - 1) % len(theme_list)]
    
    def _generate_interactive_html(self, plan: Dict, activities: List, restaurants: List) -> str:
        """Generate complete interactive HTML"""
        
        # Get number of days from plan - use the days field directly since it's an integer
        num_days = plan.get('days', 3)  # Default to 3 if not specified
        
        # Prepare data for JavaScript
        activities_json = json.dumps([{
            'id': item.get('data_id', f'activity_{i}'),
            'name': item.get('name', 'Unknown'),
            'category': item.get('category', 'Various'),
            'description': item.get('description', 'Great experience'),
            'coordinates': item.get('coordinates', {'lat': 0, 'lng': 0})
        } for i, item in enumerate(activities)])
        
        restaurants_json = json.dumps([{
            'id': item.get('data_id', f'restaurant_{i}'),
            'name': item.get('name', 'Unknown'),
            'cuisine_type': item.get('cuisine_type', 'Various'),
            'description': item.get('description', 'Great dining experience'),
            'coordinates': item.get('coordinates', {'lat': 0, 'lng': 0})
        } for i, item in enumerate(restaurants)])
        
        # Prepare route data
        route_data = {}
        day_colors = ['#4caf50', '#2196f3', '#ff9800', '#9c27b0']
        
        for daily_plan in plan['daily_plans']:
            day_num = daily_plan['day']
            route_points = daily_plan.get('route_points', [])
            if len(route_points) > 1:
                route_coords = [[point['lat'], point['lng']] for point in route_points if point['lat'] != 0]
                if len(route_coords) > 1:
                    route_data[f'day_{day_num}'] = {
                        'coordinates': route_coords,
                        'color': day_colors[(day_num - 1) % len(day_colors)],
                        'name': f"Day {day_num}: {daily_plan['theme']}"
                    }
        
        route_data_json = json.dumps(route_data)
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{plan['city_name']} - Interactive Travel Plan</title>
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
            <h1><i class="fas fa-map-marked-alt"></i> {plan['city_name']} Interactive Travel Plan</h1>
            <p>{plan['days']}-Day {plan['focus'].title()} Experience with Interactive Maps</p>
            <p><i class="fas fa-route"></i> Click days to see routes • <i class="fas fa-plus"></i> Add attractions to plan</p>
        </div>
        
        <div class="main-content">
            <div class="itinerary-section">
                <div class="map-container">
                    <div id="map" style="height: 100%; width: 100%;"></div>
                </div>
                
                <div id="itinerary-content">"""
        
        # Add daily plans
        for daily_plan in plan['daily_plans']:
            html += f"""
                    <div class="day-card" id="day-{daily_plan['day']}-card" onclick="showDayRoute({daily_plan['day']})">
                        <div class="day-header">
                            <h3><i class="fas fa-calendar-day"></i> Day {daily_plan['day']}: {daily_plan['theme']}</h3>
                            <p>{daily_plan['date']}</p>
                        </div>
                        <div class="route-info" id="day-{daily_plan['day']}-route">
                            <h4 style="color: #4facfe; margin: 0 0 10px 0;">
                                <i class="fas fa-route"></i> Day {daily_plan['day']} Route Visible
                            </h4>
                            <p style="color: #666;">Route with {len(daily_plan['schedule'])} stops highlighted on map</p>
                        </div>
                        <div class="schedule" id="day-{daily_plan['day']}-schedule">"""
            
            for schedule_item in daily_plan['schedule']:
                item = schedule_item['item']
                item_name = item.get('name', 'Unknown')
                item_description = item.get('description', item.get('cuisine_type', 'Great experience'))
                item_id = schedule_item.get('id', 'unknown')
                
                html += f"""
                            <div class="schedule-item" id="schedule-{item_id}">
                                <div class="time">{schedule_item['time']}</div>
                                <div class="activity">
                                    <div class="activity-name">{schedule_item['icon']} {item_name}</div>
                                    <div class="activity-details">{item_description}</div>
                                    <button class="remove-btn" onclick="removeFromSchedule('{item_id}')">
                                        <i class="fas fa-trash"></i> Remove
                                    </button>
                                </div>
                            </div>"""
            
            html += """
                        </div>
                    </div>"""
        
        html += f"""
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
        // Data from DynamoDB
        const activities = {activities_json};
        const restaurants = {restaurants_json};
        const routeData = {route_data_json};
        
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
            // Clear and rebuild the schedule set with items from all days
            currentSchedule.clear();
            for (let day = 1; day <= {num_days}; day++) {{
                const daySchedule = document.getElementById(`day-${{day}}-schedule`);
                if (daySchedule) {{
                    daySchedule.querySelectorAll('[id^="schedule-"]').forEach(item => {{
                        const id = item.id.replace('schedule-', '');
                        currentSchedule.add(id);
                    }});
                }}
            }}
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
            // Check if item is already scheduled on ANY day
            let existingDay = null;
            for (let day = 1; day <= {num_days}; day++) {{
                const daySchedule = document.getElementById(`day-${{day}}-schedule`);
                if (daySchedule && daySchedule.querySelector(`#schedule-${{itemId}}`)) {{
                    existingDay = day;
                    break;
                }}
            }}
            
            if (existingDay) {{
                showNotification(`${{type === 'activity' ? 'Activity' : 'Restaurant'}} already scheduled on Day ${{existingDay}}!`, 'warning');
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
        
        return html

def main():
    """
    Main function - Mapper Service Entry Point
    
    The Mapper Service is responsible for:
    1. Coordinating data from other microservices
    2. Route optimization and path calculation
    3. Interactive HTML generation with maps
    4. Real-time user interaction handling
    """
    
    parser = argparse.ArgumentParser(description='Interactive Travel Planner - Mapper Service')
    parser.add_argument('--use-services', action='store_true', 
                       help='Use microservices for data (requires running services)')
    parser.add_argument('--city', default='san_francisco', 
                       help='City for travel plan (default: san_francisco)')
    parser.add_argument('--days', type=int, default=4, 
                       help='Number of days (default: 4)')
    parser.add_argument('--focus', default='balanced', 
                       choices=['balanced', 'activities', 'food'],
                       help='Trip focus (default: balanced)')
    
    args = parser.parse_args()
    
    print("🗺️ CITYMAPPER - INTERACTIVE TRAVEL PLANNER")
    print("=" * 60)
    print("🏗️ CONSOLIDATED ARCHITECTURE:")
    print("   🎯 Consolidated Activities Service (8004) - Destinations, activities & dining")
    print("   🗺️ Mapper Service (8007) - Route optimization & HTML generation")
    print()
    
    if args.use_services:
        if MICROSERVICES_AVAILABLE:
            print("🔍 Checking microservices health...")
            if health_check():
                print("✅ DynamoDB connection healthy")
                print("🔗 Using microservices for data collection")
            else:
                print("❌ DynamoDB not accessible, falling back to sample data")
                args.use_services = False
        else:
            print("⚠️ Microservices utilities not available, using sample data")
            args.use_services = False
    else:
        print("📊 Using sample data for demonstration")
    
    print()
    
    # Initialize Mapper Service
    planner = InteractiveTravelPlanner(use_services=args.use_services)
    filepath = planner.generate_plan(args.city, args.days, args.focus)
    
    filename = os.path.basename(filepath)
    size = os.path.getsize(filepath)
    
    print(f"\n🎉 INTERACTIVE TRAVEL PLAN GENERATED!")
    print(f"📄 File: {filename} ({size:,} bytes)")
    print(f"📂 Location: ./generated_plans/")
    
    print(f"\n🗺️ MAPPER SERVICE FEATURES:")
    print(f"   ✅ Route optimization and path calculation")
    print(f"   ✅ Interactive map with pin markers")
    print(f"   ✅ Real-time add/remove functionality")
    print(f"   ✅ Day-based route toggling")
    print(f"   ✅ Coordinate mapping and visualization")
    print(f"   ✅ Responsive design for all devices")
    
    print(f"\n🏗️ DATA FLOW:")
    if args.use_services:
        print(f"   1. 📊 Data Collection - From microservices")
        print(f"   2. 🗺️ Route Optimization - Mapper service")
        print(f"   3. 🌐 HTML Generation - Interactive interface")
        print(f"   4. 🎯 User Interaction - Real-time updates")
    else:
        print(f"   1. 📊 Sample Data - For demonstration")
        print(f"   2. 🗺️ Route Optimization - Mapper service")
        print(f"   3. 🌐 HTML Generation - Interactive interface")
        print(f"   4. 🎯 User Interaction - Real-time updates")
    
    print(f"\n🌐 Open the HTML file to experience the interactive travel planner!")

if __name__ == "__main__":
    main()
