#!/usr/bin/env python3
"""Complete observability test with Langfuse + simulated RAGAS."""

import os
import time
from langfuse import Langfuse

def test_complete_observability():
    """Test complete observability stack with Langfuse + quality evaluation."""
    print("🧪 Testing Complete Observability Stack...")
    
    # Initialize Langfuse
    langfuse = Langfuse(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        host=os.getenv("LANGFUSE_HOST", "http://localhost:3000")
    )
    
    # Create trace for 3-day SFO trip
    trace_id = langfuse.create_trace_id()
    print(f"📊 Created trace ID: {trace_id}")
    
    query = "Plan a 3-day trip to San Francisco focusing on food and nature"
    
    # Create main span manually
    main_span = langfuse.start_span(
        name="citymapper_sfo_planning",
        input=query,
        metadata={
            "agent": "Citymapper Travel Agent",
            "session_id": "sfo-planning-session",
            "user_id": "travel-user",
            "tags": ["SFO", "Food", "Nature", "3-Day"]
        }
    )
        
    # MCP Tool 1: Get destination info
    span1 = langfuse.start_span(
        name="get_destination_info",
        input={"city": "san_francisco"},
        metadata={"tool": "mcp", "server": "activities"}
    )
    time.sleep(0.1)
    span1.update(output={
        "name": "San Francisco",
        "country": "USA",
        "popular_areas": ["Mission District", "Fisherman's Wharf", "Golden Gate Park"],
        "outdoor_activities": 15,
        "indoor_activities": 12
    })
    span1.end()
        
    # MCP Tool 2: Get outdoor activities
    span2 = langfuse.start_span(
        name="get_outdoor_activities",
        input={"city": "san_francisco", "category": "nature"},
        metadata={"tool": "mcp", "server": "activities"}
    )
    time.sleep(0.2)
    span2.update(output={
        "activities": [
            {"name": "Golden Gate Bridge", "duration": "2 hours", "category": "landmark"},
            {"name": "Golden Gate Park", "duration": "half-day", "category": "nature"},
            {"name": "Alcatraz Island", "duration": "half-day", "category": "historical"},
            {"name": "Presidio Trails", "duration": "3 hours", "category": "hiking"}
        ],
        "count": 4
    })
    span2.end()
        
    # MCP Tool 3: Generate interactive plan
    span3 = langfuse.start_span(
        name="generate_interactive_travel_plan",
        input={"city": "san_francisco", "days": 3, "focus": "food_and_nature"},
        metadata={"tool": "mcp", "server": "mapper"}
    )
    time.sleep(0.3)
    span3.update(output={
        "status": "generated",
        "file_size": 24576,
        "features": ["Interactive maps", "Route optimization", "POI management"],
        "html_file": "sf_3day_food_nature_plan.html"
    })
    span3.end()
        
    # Final response
    response = """# 3-Day San Francisco Food & Nature Experience

## Day 1: Golden Gate & Waterfront
- **9:00 AM**: Golden Gate Bridge walk & photos
- **12:00 PM**: Crissy Field picnic lunch
- **2:00 PM**: Golden Gate Park (Japanese Tea Garden)
- **7:00 PM**: Fisherman's Wharf seafood dinner

## Day 2: Islands & Hills  
- **9:00 AM**: Alcatraz Island tour
- **1:00 PM**: North Beach Italian lunch
- **3:00 PM**: Lombard Street & Coit Tower
- **7:00 PM**: Mission District food tour

## Day 3: Parks & Markets
- **9:00 AM**: Presidio trails & nature walks
- **12:00 PM**: Presidio picnic lunch
- **2:00 PM**: Chinatown exploration
- **4:00 PM**: Ferry Building Marketplace
- **7:00 PM**: Sunset dinner at Pier 39

🗺️ Interactive HTML plan includes real-time maps, weather integration, and dining recommendations near each activity."""

    # Update main span with final response
    main_span.update(
        output=response,
        metadata={
            "response_length": len(response),
            "tools_used": 3,
            "execution_time_ms": 600,
            "plan_type": "3_day_sfo_food_nature"
        }
    )
    main_span.end()
    
    # Simulate RAGAS quality evaluation scores
    print("📊 Simulating RAGAS Quality Evaluation...")
    
    # Faithfulness score (how accurate to source data)
    langfuse.create_score(
        trace_id=trace_id,
        name="faithfulness",
        value=0.94,
        comment="High accuracy - all locations and activities are real and correctly described"
    )
    
    # Answer relevancy score (how well it matches the query)
    langfuse.create_score(
        trace_id=trace_id,
        name="answer_relevancy", 
        value=0.91,
        comment="Excellent relevancy - perfectly balances food and nature as requested"
    )
    
    # Context precision score (how well tools were used)
    langfuse.create_score(
        trace_id=trace_id,
        name="context_precision",
        value=0.89,
        comment="Good tool usage - effectively used destination, activities, and planning tools"
    )
    
    # Overall quality score
    overall_score = (0.94 + 0.91 + 0.89) / 3
    langfuse.create_score(
        trace_id=trace_id,
        name="overall_quality",
        value=overall_score,
        comment=f"Comprehensive 3-day SFO plan with excellent food/nature balance (avg: {overall_score:.3f})"
    )
    
    # Flush data
    langfuse.flush()
    
    print("✅ Complete observability test successful!")
    print(f"📊 Trace ID: {trace_id}")
    print("📋 Generated:")
    print("   - 1 main travel planning trace")
    print("   - 3 MCP tool execution spans")
    print("   - 4 quality evaluation scores")
    print("   - Complete 3-day SFO food & nature plan")
    print()
    print("🔗 Check Langfuse UI: http://localhost:3000")
    print("   Look for trace: 'citymapper_sfo_planning'")
    
    return trace_id, overall_score

if __name__ == "__main__":
    if not os.getenv("LANGFUSE_PUBLIC_KEY"):
        print("❌ Please set LANGFUSE_PUBLIC_KEY environment variable")
        exit(1)
    
    try:
        trace_id, score = test_complete_observability()
        print(f"\n🎉 COMPLETE OBSERVABILITY: SUCCESS!")
        print(f"📊 Trace ID: {trace_id}")
        print(f"⭐ Quality Score: {score:.3f}/1.0")
    except Exception as e:
        print(f"\n❌ COMPLETE OBSERVABILITY: FAILED!")
        print(f"Error: {e}")