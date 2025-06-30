#!/usr/bin/env python3
"""
Data Migration Script - JSON to DynamoDB
Migrates all service data from JSON files to single DynamoDB table
"""
import os
import sys
import json
import logging
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from utils.dynamodb_utils import (
    initialize_dynamodb,
    put_item,
    health_check,
    get_activities_by_city,
    get_food_by_city
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def migrate_service_data(service_name: str, json_file_path: str, data_key: str):
    """Migrate data for a specific service"""
    logger.info(f"🔄 Migrating {service_name} data from {json_file_path}")
    
    if not os.path.exists(json_file_path):
        logger.warning(f"⚠️ JSON file not found: {json_file_path}")
        return 0
    
    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        
        migrated_count = 0
        cities = data.get('cities', {})
        
        for city_id, city_data in cities.items():
            items = city_data.get(data_key, [])
            logger.info(f"   📊 Found {len(items)} {service_name} items for {city_id}")
            
            for item in items:
                item_id = item.get('id', f"{service_name}_{migrated_count}")
                
                # Add service-specific metadata
                item['service'] = service_name
                item['city'] = city_id
                
                if put_item(city_id, service_name, item_id, item):
                    migrated_count += 1
                else:
                    logger.error(f"❌ Failed to migrate item: {item_id}")
        
        logger.info(f"✅ Migrated {migrated_count} {service_name} items")
        return migrated_count
        
    except Exception as e:
        logger.error(f"❌ Error migrating {service_name} data: {e}")
        return 0

def main():
    """Main migration function"""
    logger.info("🚀 CITYMAPPER DATA MIGRATION - JSON TO DYNAMODB")
    logger.info("=" * 60)
    
    # Check DynamoDB health
    logger.info("🔍 Checking DynamoDB connection...")
    if not health_check():
        logger.error("❌ DynamoDB not accessible")
        logger.info("💡 Make sure DynamoDB Local is running: docker-compose up dynamodb-local")
        return
    
    logger.info("✅ DynamoDB connection healthy")
    
    # Initialize DynamoDB
    logger.info("🏗️ Initializing DynamoDB table...")
    if not initialize_dynamodb():
        logger.error("❌ Failed to initialize DynamoDB")
        return
    
    logger.info("✅ DynamoDB table ready")
    
    # Define service migrations
    services_to_migrate = [
        {
            'name': 'activities',
            'file': 'src/mcp_servers/activities/activities_data.json',
            'data_key': 'activities'
        },
        {
            'name': 'food',
            'file': 'src/mcp_servers/food/food_data.json',
            'data_key': 'restaurants'
        },
        {
            'name': 'travel',
            'file': 'src/mcp_servers/travel/travel_data.json',
            'data_key': 'hotels'
        },
        {
            'name': 'weather',
            'file': 'src/mcp_servers/weather/weather_data.json',
            'data_key': 'weather'
        },
        {
            'name': 'maps',
            'file': 'src/mcp_servers/maps/maps_data.json',
            'data_key': 'routes'
        },
        {
            'name': 'visualization',
            'file': 'src/mcp_servers/visualization/visualization_data.json',
            'data_key': 'charts'
        }
    ]
    
    # Migrate each service
    total_migrated = 0
    logger.info("📊 Starting data migration...")
    
    for service in services_to_migrate:
        count = migrate_service_data(
            service['name'],
            service['file'],
            service['data_key']
        )
        total_migrated += count
    
    logger.info("=" * 60)
    logger.info(f"🎉 MIGRATION COMPLETE!")
    logger.info(f"📊 Total items migrated: {total_migrated}")
    
    # Verify migration
    logger.info("🔍 Verifying migration...")
    activities = get_activities_by_city('san_francisco')
    restaurants = get_food_by_city('san_francisco')
    
    logger.info(f"✅ Verification results:")
    logger.info(f"   🎯 Activities: {len(activities)} items")
    logger.info(f"   🍽️ Restaurants: {len(restaurants)} items")
    
    if activities or restaurants:
        logger.info("✅ Migration successful - data is accessible!")
    else:
        logger.warning("⚠️ No data found - check migration logs")
    
    logger.info("🌐 Services can now use DynamoDB for data storage!")

if __name__ == "__main__":
    main()
