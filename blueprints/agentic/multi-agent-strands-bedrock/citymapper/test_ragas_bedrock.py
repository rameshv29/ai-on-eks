#!/usr/bin/env python3
"""Test RAGAS evaluation with Bedrock."""

import os
from observability import observability

def test_ragas_with_bedrock():
    """Test RAGAS evaluation using Bedrock LLM."""
    print("🧪 Testing RAGAS with Bedrock...")
    
    # Set AWS region
    os.environ["AWS_REGION"] = "us-west-2"
    
    # Test query and response
    query = "Plan a 3-day trip to San Francisco focusing on food and nature"
    response = """# 3-Day San Francisco Food & Nature Experience

## Day 1: Golden Gate & Nature
- Morning: Golden Gate Bridge walk
- Afternoon: Golden Gate Park exploration
- Evening: Local dining in Fisherman's Wharf

## Day 2: Urban Nature & Food Scene  
- Morning: Alcatraz Island tour
- Afternoon: Lombard Street & Coit Tower
- Evening: Mission District food tour

## Day 3: Parks & Local Cuisine
- Morning: Presidio trails
- Afternoon: Chinatown exploration
- Evening: Ferry Building food market"""

    context = [
        "San Francisco has Golden Gate Bridge and Golden Gate Park",
        "Mission District is known for food tours",
        "Alcatraz Island offers historical tours",
        "Ferry Building has a famous food marketplace"
    ]
    
    print(f"📤 Query: {query}")
    print(f"📋 Response length: {len(response)} characters")
    print(f"🔧 Context items: {len(context)}")
    print()
    
    try:
        print("🚀 Running RAGAS evaluation with Bedrock...")
        scores = observability.evaluate_response_quality(
            query=query,
            response=response,
            context=context
        )
        
        if scores:
            print("✅ RAGAS evaluation successful!")
            print("📊 Quality Scores:")
            for metric, score in scores.items():
                print(f"   - {metric}: {score:.3f}")
            
            avg_score = sum(scores.values()) / len(scores)
            print(f"📈 Average Score: {avg_score:.3f}")
            
            return True
        else:
            print("⚠️ RAGAS evaluation returned empty scores")
            return False
            
    except Exception as e:
        print(f"❌ RAGAS evaluation failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 RAGAS + Bedrock Integration Test")
    print("=" * 50)
    
    success = test_ragas_with_bedrock()
    
    print()
    if success:
        print("🎉 RAGAS with Bedrock: SUCCESS!")
    else:
        print("❌ RAGAS with Bedrock: FAILED!")
        print("💡 Note: Requires valid AWS credentials for Bedrock access")