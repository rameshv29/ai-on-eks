#!/usr/bin/env python3
"""Working Langfuse test using correct API."""

import os
from langfuse import Langfuse

def test_langfuse_e2e():
    """Test end-to-end Langfuse observability for travel planning."""
    print("🧪 Testing E2E Langfuse Observability...")
    
    # Initialize Langfuse client
    langfuse = Langfuse(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        host=os.getenv("LANGFUSE_HOST", "http://localhost:3000")
    )
    
    print("✅ Langfuse client initialized")
    
    # Create trace ID
    trace_id = langfuse.create_trace_id()
    print(f"📊 Created trace ID: {trace_id}")
    
    # Start main trace
    with langfuse.start_span(
        name="citymapper_travel_planning",
        trace_id=trace_id,
        input="Plan a 3-day trip to San Francisco focusing on food and nature",
        metadata={
            "agent": "Citymapper Travel Agent",
            "session_id": "test-session-123",
            "user_id": "test-user"
        }
    ) as main_span:
        
        # Tool 1: Get destination info
        with langfuse.start_span(
            name="get_destination_info",
            trace_id=trace_id,
            input={"city": "san_francisco"},
            metadata={"tool_type": "mcp", "server": "activities"}
        ) as span1:
            span1.update(output={
                "name": "San Francisco",
                "country": "USA",
                "description": "Beautiful city with Golden Gate Bridge",
                "total_outdoor_activities": 15
            })
        
        # Tool 2: Get outdoor activities
        with langfuse.start_span(
            name="get_outdoor_activities",
            trace_id=trace_id,
            input={"city": "san_francisco", "category": "nature"},
            metadata={"tool_type": "mcp", "server": "activities"}
        ) as span2:
            span2.update(output={
                "activities": [
                    {"name": "Golden Gate Park", "duration": "half-day"},
                    {"name": "Golden Gate Bridge", "duration": "short"},
                    {"name": "Alcatraz Island", "duration": "half-day"}
                ],
                "count": 3
            })
        
        # Tool 3: Generate travel plan
        with langfuse.start_span(
            name="generate_interactive_travel_plan",
            trace_id=trace_id,
            input={"city": "san_francisco", "days": 3, "focus": "food_and_nature"},
            metadata={"tool_type": "mcp", "server": "mapper"}
        ) as span3:
            span3.update(output={
                "status": "generated",
                "file_size": 24576,
                "features": ["Interactive maps", "Route optimization"],
                "html_file": "san_francisco_3day_food_nature_plan.html"
            })
        
        # Update main span with final response
        response = """# 3-Day San Francisco Food & Nature Experience

## Day 1: Golden Gate & Nature
- **Morning**: Golden Gate Bridge walk
- **Afternoon**: Golden Gate Park exploration  
- **Evening**: Local dining in Fisherman's Wharf

## Day 2: Urban Nature & Food Scene
- **Morning**: Alcatraz Island tour
- **Afternoon**: Lombard Street & Coit Tower
- **Evening**: Mission District food tour

## Day 3: Parks & Local Cuisine
- **Morning**: Presidio trails
- **Afternoon**: Chinatown exploration
- **Evening**: Ferry Building food market

🗺️ Interactive HTML plan generated with maps and route optimization."""
        
        main_span.update(
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
        trace_id=trace_id,
        name="travel_plan_quality",
        value=0.92,
        comment="High quality plan with good balance of food and nature activities"
    )
    
    # Flush to ensure data is sent
    langfuse.flush()
    
    print("✅ E2E travel planning trace created successfully!")
    print(f"📊 Trace ID: {trace_id}")
    print("📋 Trace includes:")
    print("   - Main travel planning span")
    print("   - 3 MCP tool call spans")
    print("   - Quality evaluation score")
    print()
    print("🔗 Check Langfuse UI: http://localhost:3000")
    print("   Look for trace: 'citymapper_travel_planning'")
    
    return trace_id

if __name__ == "__main__":
    if not os.getenv("LANGFUSE_PUBLIC_KEY"):
        print("❌ Please set LANGFUSE_PUBLIC_KEY environment variable")
        exit(1)
    
    try:
        trace_id = test_langfuse_e2e()
        print(f"\n🎉 E2E Observability Test: SUCCESS!")
        print(f"📋 Trace ID: {trace_id}")
    except Exception as e:
        print(f"\n❌ E2E Observability Test: FAILED!")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()