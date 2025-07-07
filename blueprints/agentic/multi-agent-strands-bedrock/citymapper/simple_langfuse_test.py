#!/usr/bin/env python3
"""Simple Langfuse test to verify observability is working."""

import os
from langfuse import Langfuse

def test_langfuse_connection():
    """Test basic Langfuse connection and trace creation."""
    print("🧪 Testing Langfuse Connection...")
    
    try:
        # Initialize Langfuse client
        langfuse = Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_HOST", "http://localhost:3000")
        )
        
        print("✅ Langfuse client initialized")
        
        # Test basic functionality
        print("📊 Testing trace creation...")
        
        # Use the correct API based on Langfuse version
        try:
            # Try newer API first
            trace = langfuse.trace(
                name="citymapper_test_trace",
                input="Test travel planning query",
                output="Test travel plan response",
                metadata={
                    "agent": "Citymapper Travel Agent",
                    "test": True
                }
            )
            print("✅ Trace created successfully (new API)")
            
        except Exception as e:
            print(f"⚠️ New API failed: {e}")
            # Try alternative approach
            try:
                # Manual trace creation
                import uuid
                trace_id = str(uuid.uuid4())
                
                # Send trace data
                langfuse.trace(
                    id=trace_id,
                    name="citymapper_test_trace",
                    input="Test travel planning query",
                    output="Test travel plan response"
                )
                print("✅ Trace created successfully (manual)")
                
            except Exception as e2:
                print(f"❌ Both methods failed: {e2}")
                return False
        
        # Flush to ensure data is sent
        langfuse.flush()
        print("✅ Data flushed to Langfuse")
        
        print()
        print("🎉 Langfuse Integration Test: SUCCESS!")
        print("🔗 Check Langfuse UI: http://localhost:3000")
        print("   Look for trace: 'citymapper_test_trace'")
        
        return True
        
    except Exception as e:
        print(f"❌ Langfuse test failed: {e}")
        return False

if __name__ == "__main__":
    if not os.getenv("LANGFUSE_PUBLIC_KEY"):
        print("❌ Please set LANGFUSE_PUBLIC_KEY environment variable")
        exit(1)
    
    success = test_langfuse_connection()
    if success:
        print("\n✅ E2E Observability: WORKING!")
    else:
        print("\n❌ E2E Observability: FAILED!")