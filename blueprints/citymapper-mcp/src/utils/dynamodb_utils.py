"""
DynamoDB utilities for Citymapper microservices
Single table design with proper partition and sort keys
"""
import boto3
import json
import os
import logging
from typing import Dict, List, Any, Optional
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# DynamoDB configuration
TABLE_NAME = "citymapper-data"
REGION = os.getenv('AWS_REGION', 'us-east-1')
ENDPOINT_URL = os.getenv('DYNAMODB_ENDPOINT_URL', 'http://localhost:8000')

# Initialize DynamoDB client
def get_dynamodb_client():
    """Get DynamoDB client with proper configuration"""
    return boto3.client(
        'dynamodb',
        region_name=REGION,
        endpoint_url=ENDPOINT_URL,
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID', 'dummy'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY', 'dummy')
    )

def get_dynamodb_resource():
    """Get DynamoDB resource with proper configuration"""
    return boto3.resource(
        'dynamodb',
        region_name=REGION,
        endpoint_url=ENDPOINT_URL,
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID', 'dummy'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY', 'dummy')
    )

def create_table_if_not_exists():
    """Create the citymapper-data table if it doesn't exist"""
    try:
        dynamodb = get_dynamodb_client()
        
        # Check if table exists
        try:
            dynamodb.describe_table(TableName=TABLE_NAME)
            logger.info(f"Table {TABLE_NAME} already exists")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceNotFoundException':
                raise
        
        # Create table
        logger.info(f"Creating table {TABLE_NAME}...")
        dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {
                    'AttributeName': 'PK',
                    'KeyType': 'HASH'  # Partition key
                },
                {
                    'AttributeName': 'SK',
                    'KeyType': 'RANGE'  # Sort key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'PK',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'SK',
                    'AttributeType': 'S'
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Wait for table to be created
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName=TABLE_NAME)
        
        logger.info(f"Table {TABLE_NAME} created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error creating table: {e}")
        return False

def health_check() -> bool:
    """Check if DynamoDB is accessible"""
    try:
        dynamodb = get_dynamodb_client()
        dynamodb.list_tables()
        return True
    except Exception as e:
        logger.error(f"DynamoDB health check failed: {e}")
        return False

# Single table design functions
def put_item(city_id: str, service: str, item_id: str, data: Dict[str, Any]) -> bool:
    """Put an item into the single table"""
    try:
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table(TABLE_NAME)
        
        import time
        
        item = {
            'PK': f'CITY#{city_id}',
            'SK': f'{service.upper()}#{item_id}',
            'service': service,
            'city_id': city_id,
            'item_id': item_id,
            'data': data,
            'created_at': str(int(time.time()))
        }
        
        table.put_item(Item=item)
        return True
        
    except Exception as e:
        logger.error(f"Error putting item: {e}")
        return False

def get_items_by_service(city_id: str, service: str) -> List[Dict[str, Any]]:
    """Get all items for a specific service and city"""
    try:
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table(TABLE_NAME)
        
        response = table.query(
            KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
            ExpressionAttributeValues={
                ':pk': f'CITY#{city_id}',
                ':sk': f'{service.upper()}#'
            }
        )
        
        items = []
        for item in response.get('Items', []):
            # Add the item_id to the data for compatibility
            data = item.get('data', {})
            data['data_id'] = item.get('item_id')
            items.append(data)
        
        return items
        
    except Exception as e:
        logger.error(f"Error getting items for service {service}: {e}")
        return []

def get_item(city_id: str, service: str, item_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific item"""
    try:
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table(TABLE_NAME)
        
        response = table.get_item(
            Key={
                'PK': f'CITY#{city_id}',
                'SK': f'{service.upper()}#{item_id}'
            }
        )
        
        if 'Item' in response:
            data = response['Item'].get('data', {})
            data['data_id'] = response['Item'].get('item_id')
            return data
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting item {item_id}: {e}")
        return None

# Service-specific helper functions
def get_activities_by_city(city_id: str) -> List[Dict[str, Any]]:
    """Get all activities for a city"""
    return get_items_by_service(city_id, 'activities')

def get_food_by_city(city_id: str) -> List[Dict[str, Any]]:
    """Get all restaurants for a city"""
    return get_items_by_service(city_id, 'food')

def get_travel_by_city(city_id: str) -> List[Dict[str, Any]]:
    """Get all travel options for a city"""
    return get_items_by_service(city_id, 'travel')

def get_weather_by_city(city_id: str) -> List[Dict[str, Any]]:
    """Get weather data for a city"""
    return get_items_by_service(city_id, 'weather')

def get_maps_by_city(city_id: str) -> List[Dict[str, Any]]:
    """Get maps data for a city"""
    return get_items_by_service(city_id, 'maps')

def get_visualization_by_city(city_id: str) -> List[Dict[str, Any]]:
    """Get visualization data for a city"""
    return get_items_by_service(city_id, 'visualization')

# Data migration functions
def migrate_json_to_dynamodb(json_file_path: str, service: str) -> bool:
    """Migrate data from JSON file to DynamoDB"""
    try:
        if not os.path.exists(json_file_path):
            logger.warning(f"JSON file {json_file_path} not found")
            return False
        
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        
        cities = data.get('cities', {})
        migrated_count = 0
        
        for city_id, city_data in cities.items():
            # Get the appropriate data key based on service
            service_key = {
                'activities': 'activities',
                'food': 'restaurants',
                'travel': 'hotels',
                'weather': 'weather',
                'maps': 'routes',
                'visualization': 'charts'
            }.get(service, service)
            
            items = city_data.get(service_key, [])
            
            for item in items:
                item_id = item.get('id', f"{service}_{migrated_count}")
                if put_item(city_id, service, item_id, item):
                    migrated_count += 1
        
        logger.info(f"Migrated {migrated_count} items for service {service}")
        return True
        
    except Exception as e:
        logger.error(f"Error migrating data for service {service}: {e}")
        return False

def initialize_dynamodb():
    """Initialize DynamoDB table and migrate data if needed"""
    logger.info("Initializing DynamoDB...")
    
    # Create table if it doesn't exist
    if not create_table_if_not_exists():
        logger.error("Failed to create DynamoDB table")
        return False
    
    logger.info("DynamoDB initialization complete")
    return True

# Initialize on import
if __name__ == "__main__":
    initialize_dynamodb()
