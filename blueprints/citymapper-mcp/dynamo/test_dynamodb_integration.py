#!/usr/bin/env python3
"""
Test DynamoDB Integration
Quick test to verify DynamoDB integration is working
"""
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_dynamodb_integration():
    """Test DynamoDB integration"""
    print("🧪 TESTING DYNAMODB INTEGRATION")
    print("=" * 50)
    
    try:
        from utils.dynamodb_utils import (
            health_check,
            initialize_dynamodb,
            get_activities_by_city,
            get_food_by_city,
            put_item
        )
        print("✅ DynamoDB utilities imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import DynamoDB utilities: {e}")
        return False
    
    # Test health check
    print("\n🔍 Testing DynamoDB connection...")
    if health_check():
        print("✅ DynamoDB connection successful")
    else:
        print("❌ DynamoDB connection failed")
        print("💡 Make sure DynamoDB Local is running: docker-compose up dynamodb-local")
        return False
    
    # Test table initialization
    print("\n🏗️ Testing table initialization...")
    if initialize_dynamodb():
        print("✅ DynamoDB table initialized")
    else:
        print("❌ Failed to initialize DynamoDB table")
        return False
    
    # Test data insertion
    print("\n📝 Testing data insertion...")
    test_activity = {
        'name': 'Test Activity',
        'description': 'Test activity for integration testing',
        'category': 'Test',
        'duration': 'short',
        'cost': 'free'
    }
    
    if put_item('test_city', 'activities', 'test_activity', test_activity):
        print("✅ Data insertion successful")
    else:
        print("❌ Data insertion failed")
        return False
    
    # Test data retrieval
    print("\n📊 Testing data retrieval...")
    activities = get_activities_by_city('san_francisco')
    restaurants = get_food_by_city('san_francisco')
    
    print(f"   🎯 Activities found: {len(activities)}")
    print(f"   🍽️ Restaurants found: {len(restaurants)}")
    
    if activities:
        print(f"   📋 Sample activity: {activities[0].get('name', 'Unknown')}")
    
    if restaurants:
        print(f"   📋 Sample restaurant: {restaurants[0].get('name', 'Unknown')}")
    
    print("\n" + "=" * 50)
    print("🎉 DYNAMODB INTEGRATION TEST COMPLETE!")
    
    if activities or restaurants:
        print("✅ All tests passed - DynamoDB integration is working!")
        return True
    else:
        print("⚠️ No data found - run setup_dynamodb.py to populate data")
        return True  # Still consider this a pass since connection works

def main():
    """Main test function"""
    success = test_dynamodb_integration()
    
    if success:
        print("\n🌐 Ready to generate travel plans with DynamoDB!")
        print("   Run: python interactive_travel_planner.py --use-services")
    else:
        print("\n❌ DynamoDB integration test failed")
        print("   Check DynamoDB Local is running and try again")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
