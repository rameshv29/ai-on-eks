#!/usr/bin/env python3
"""Test Langfuse integration with Citymapper agent."""

import os
import time
from langfuse import Langfuse

def test_langfuse_direct():
    """Test Langfuse integration directly."""
    print("🧪 Testing Direct Langfuse Integration...")
    
    # Initialize Langfuse client
    langfuse = Langfuse(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        host=os.getenv("LANGFUSE_HOST", "http://localhost:3000")
    )
    
    # Create a trace for travel planning
    trace = langfuse.create_trace(
        name="citymapper_travel_planning",
        input="Plan a 3-day trip to San Francisco focusing on food and nature",
        metadata={
            "agent": "Citymapper Travel Agent",
            "session_id": "test-session-123",
            "user_id": "test-user"
        },
        tags=["Citymapper-Agent", "Travel-Planning", "E2E-Test"]
    )
    
    # Simulate MCP tool calls as spans
    span1 = langfuse.create_span(
        trace_id=trace.id,
        name="get_destination_info",
        input={"city": "san_francisco"},
        metadata={"tool_type": "mcp", "server": "activities"}
    )
    time.sleep(0.1)  # Simulate processing
    span1.end(output={
        "name": "San Francisco",
        "country": "USA", 
        "description": "Beautiful city with Golden Gate Bridge",
        "total_outdoor_activities": 15
    })
    
    span2 = langfuse.create_span(
        trace_id=trace.id,
        name="get_outdoor_activities", 
        input={"city": "san_francisco", "category": "nature"},
        metadata={"tool_type": "mcp", "server": "activities"}
    )
    time.sleep(0.2)  # Simulate processing
    span2.end(output={
        "activities": [
            {"name": "Golden Gate Park", "duration": "half-day"},
            {"name": "Golden Gate Bridge", "duration": "short"},
            {"name": "Alcatraz Island", "duration": "half-day"}
        ],
        "count": 3
    })
    
    span3 = langfuse.create_span(
        trace_id=trace.id,
        name="generate_interactive_travel_plan",
        input={"city": "san_francisco", "days": 3, "focus": "food_and_nature"},
        metadata={"tool_type": "mcp", "server": "mapper"}
    )
    time.sleep(0.3)  # Simulate processing
    span3.end(output={
        "status": "generated",
        "file_size": 24576,
        "features": ["Interactive maps", "Route optimization", "POI management"],
        "html_file": "san_francisco_3day_food_nature_plan.html"
    })
    
    # Complete the trace with final response
    response = """# 3-Day San Francisco Food & Nature Experience

## Day 1: Golden Gate & Nature
- **Morning**: Golden Gate Bridge walk and photo session
- **Afternoon**: Golden Gate Park exploration (Japanese Tea Garden, Conservatory)
- **Evening**: Local dining in Fisherman's Wharf

## Day 2: Urban Nature & Food Scene  
- **Morning**: Alcatraz Island tour with audio guide
- **Afternoon**: Lombard Street (most crooked street) & Coit Tower
- **Evening**: Mission District food tour (tacos, craft beer)

## Day 3: Parks & Local Cuisine
- **Morning**: Presidio trails and nature walks
- **Afternoon**: Chinatown exploration and dim sum
- **Evening**: Ferry Building Marketplace food sampling

🗺️ **Interactive HTML plan generated** with:
- Real-time maps with route optimization
- Add/remove POI functionality  
- Dining recommendations near each activity
- Weather-aware scheduling"""

    trace.update(
        output=response,
        metadata={
            "response_length": len(response),
            "tools_used": 3,
            "execution_time_ms": 600,
            "plan_type": "3_day_sfo_food_nature"
        }
    )
    
    # Add evaluation score
    langfuse.create_score(
        trace_id=trace.id,
        name="travel_plan_quality",
        value=0.92,
        comment="High quality plan with good balance of food and nature activities"
    )
    
    print("✅ Langfuse trace created successfully!")
    print(f"📊 Trace ID: {trace.id}")
    print("🔗 Check Langfuse UI: http://localhost:3000")
    print("   Look for trace: 'citymapper_travel_planning'")
    
    return trace.id

if __name__ == "__main__":
    if not os.getenv("LANGFUSE_PUBLIC_KEY"):
        print("❌ Please set LANGFUSE_PUBLIC_KEY environment variable")
        exit(1)
    
    trace_id = test_langfuse_direct()
    print(f"\n🎉 E2E Observability Test Complete!")
    print(f"📋 Trace ID: {trace_id}")