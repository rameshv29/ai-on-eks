#!/usr/bin/env python3
"""
DynamoDB Setup and Data Migration Script
Sets up DynamoDB Local and migrates all service data from JSON files
"""
import os
import sys
import time
import subprocess
import logging
from decimal import Decimal

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.dynamodb_utils import (
    initialize_dynamodb,
    health_check,
    put_item,
    get_activities_by_city,
    get_food_by_city
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def wait_for_dynamodb(max_attempts=30, delay=2):
    """Wait for DynamoDB Local to be ready"""
    logger.info("🔍 Waiting for DynamoDB Local to be ready...")
    
    for attempt in range(max_attempts):
        if health_check():
            logger.info("✅ DynamoDB Local is ready!")
            return True
        
        logger.info(f"   Attempt {attempt + 1}/{max_attempts} - waiting {delay}s...")
        time.sleep(delay)
    
    logger.error("❌ DynamoDB Local failed to start")
    return False

def populate_sample_data():
    """Populate DynamoDB with sample data for San Francisco"""
    logger.info("📊 Populating DynamoDB with sample data...")
    
    # Sample activities data
    activities = [
        {
            'id': 'alcatraz_island',
            'name': 'Alcatraz Island',
            'description': 'Famous former federal prison on an island',
            'category': 'Historical',
            'duration': 'half-day',
            'cost': 'medium',
            'categories': ['historical', 'island', 'tour']
        },
        {
            'id': 'golden_gate_bridge',
            'name': 'Golden Gate Bridge',
            'description': 'Iconic suspension bridge',
            'category': 'Landmark',
            'duration': 'short',
            'cost': 'free',
            'categories': ['landmark', 'photography', 'outdoor']
        },
        {
            'id': 'golden_gate_park',
            'name': 'Golden Gate Park',
            'description': 'Large urban park with gardens and museums',
            'category': 'Nature',
            'duration': 'full-day',
            'cost': 'low',
            'categories': ['nature', 'park', 'outdoor', 'garden']
        },
        {
            'id': 'fishermans_wharf',
            'name': "Fisherman's Wharf",
            'description': 'Waterfront area with shops and restaurants',
            'category': 'Entertainment',
            'duration': 'half-day',
            'cost': 'medium',
            'categories': ['entertainment', 'waterfront', 'shopping']
        },
        {
            'id': 'lombard_street',
            'name': 'Lombard Street',
            'description': 'The most crooked street in the world',
            'category': 'Landmark',
            'duration': 'short',
            'cost': 'free',
            'categories': ['landmark', 'photography', 'unique']
        },
        {
            'id': 'pier_39',
            'name': 'Pier 39',
            'description': 'Shopping center and popular tourist attraction',
            'category': 'Entertainment',
            'duration': 'half-day',
            'cost': 'medium',
            'categories': ['entertainment', 'shopping', 'waterfront']
        },
        {
            'id': 'cable_car_ride',
            'name': 'Cable Car Ride',
            'description': 'Historic cable car system',
            'category': 'Transportation',
            'duration': 'short',
            'cost': 'low',
            'categories': ['transportation', 'historical', 'experience']
        },
        {
            'id': 'muir_woods',
            'name': 'Muir Woods',
            'description': 'National monument with ancient redwood trees',
            'category': 'Nature',
            'duration': 'full-day',
            'cost': 'medium',
            'categories': ['nature', 'hiking', 'outdoor', 'forest']
        },
        {
            'id': 'palace_of_fine_arts',
            'name': 'Palace of Fine Arts',
            'description': 'Monumental structure built for 1915 exposition',
            'category': 'Architecture',
            'duration': 'short',
            'cost': 'free',
            'categories': ['architecture', 'historical', 'photography']
        },
        {
            'id': 'exploratorium',
            'name': 'Exploratorium',
            'description': 'Interactive science museum',
            'category': 'Museum',
            'duration': 'half-day',
            'cost': 'medium',
            'categories': ['museum', 'science', 'family', 'interactive']
        }
    ]
    
    # Sample restaurants data
    restaurants = [
        {
            'id': 'tartine_bakery',
            'name': 'Tartine Bakery',
            'description': 'Famous artisanal bakery and cafe',
            'cuisine_type': 'Bakery',
            'price_range': 'medium',
            'rating': Decimal('4.5'),
            'categories': ['bakery', 'cafe', 'breakfast']
        },
        {
            'id': 'zuni_cafe',
            'name': 'Zuni Cafe',
            'description': 'Iconic restaurant known for roast chicken',
            'cuisine_type': 'Mediterranean',
            'price_range': 'high',
            'rating': Decimal('4.7'),
            'categories': ['mediterranean', 'fine-dining', 'chicken']
        },
        {
            'id': 'la_taqueria',
            'name': 'La Taqueria',
            'description': 'Authentic Mission-style burritos',
            'cuisine_type': 'Mexican',
            'price_range': 'low',
            'rating': Decimal('4.6'),
            'categories': ['mexican', 'burritos', 'casual']
        },
        {
            'id': 'liholiho_yacht_club',
            'name': 'Liholiho Yacht Club',
            'description': 'Modern Hawaiian cuisine',
            'cuisine_type': 'Hawaiian',
            'price_range': 'high',
            'rating': Decimal('4.4'),
            'categories': ['hawaiian', 'modern', 'seafood']
        },
        {
            'id': 'delfina',
            'name': 'Delfina',
            'description': 'Neighborhood Italian restaurant',
            'cuisine_type': 'Italian',
            'price_range': 'medium',
            'rating': Decimal('4.3'),
            'categories': ['italian', 'neighborhood', 'pasta']
        }
    ]
    
    # Insert activities
    activities_count = 0
    for activity in activities:
        if put_item('san_francisco', 'activities', activity['id'], activity):
            activities_count += 1
    
    # Insert restaurants
    restaurants_count = 0
    for restaurant in restaurants:
        if put_item('san_francisco', 'food', restaurant['id'], restaurant):
            restaurants_count += 1
    
    logger.info(f"✅ Populated {activities_count} activities and {restaurants_count} restaurants")
    return activities_count + restaurants_count > 0

def verify_data():
    """Verify that data was inserted correctly"""
    logger.info("🔍 Verifying data insertion...")
    
    activities = get_activities_by_city('san_francisco')
    restaurants = get_food_by_city('san_francisco')
    
    logger.info(f"   🎯 Activities found: {len(activities)}")
    logger.info(f"   🍽️ Restaurants found: {len(restaurants)}")
    
    if activities:
        logger.info(f"   📋 Sample activity: {activities[0].get('name', 'Unknown')}")
    
    if restaurants:
        logger.info(f"   📋 Sample restaurant: {restaurants[0].get('name', 'Unknown')}")
    
    return len(activities) > 0 and len(restaurants) > 0

def main():
    """Main setup function"""
    logger.info("🚀 DYNAMODB SETUP AND DATA MIGRATION")
    logger.info("=" * 60)
    
    # Check if DynamoDB is already running
    if health_check():
        logger.info("✅ DynamoDB Local is already running")
    else:
        logger.info("❌ DynamoDB Local is not running")
        logger.info("💡 Start DynamoDB Local with: docker-compose up dynamodb-local")
        logger.info("   Or run full stack: docker-compose up -d")
        return False
    
    # Initialize DynamoDB table
    logger.info("🏗️ Initializing DynamoDB table...")
    if not initialize_dynamodb():
        logger.error("❌ Failed to initialize DynamoDB")
        return False
    
    logger.info("✅ DynamoDB table initialized")
    
    # Populate with sample data
    if not populate_sample_data():
        logger.error("❌ Failed to populate sample data")
        return False
    
    # Verify data
    if not verify_data():
        logger.error("❌ Data verification failed")
        return False
    
    logger.info("=" * 60)
    logger.info("🎉 SETUP COMPLETE!")
    logger.info("✅ DynamoDB Local is ready")
    logger.info("✅ Sample data populated")
    logger.info("✅ All services can now use DynamoDB")
    
    logger.info("\n🌐 Next steps:")
    logger.info("   1. Generate travel plan: python interactive_travel_planner.py --use-services")
    logger.info("   2. Or use Docker: docker-compose exec mapper-service python interactive_travel_planner.py --use-services")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
