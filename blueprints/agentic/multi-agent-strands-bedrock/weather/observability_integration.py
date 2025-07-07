"""Observability integration for Weather Agent."""

import os
import sys
from functools import wraps

# Add citymapper observability to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../citymapper'))

try:
    from observability import observability, trace_agent_call
except ImportError:
    # Fallback if observability not available
    def trace_agent_call(agent_name: str):
        def decorator(func):
            return func
        return decorator
    
    class MockObservability:
        def trace_agent_request(self, *args, **kwargs):
            pass
        def evaluate_response_quality(self, *args, **kwargs):
            return {}
    
    observability = MockObservability()


def add_weather_observability(agent_func):
    """Add observability to weather agent function."""
    @trace_agent_call("Weather Agent")
    @wraps(agent_func)
    def wrapper(*args, **kwargs):
        result = agent_func(*args, **kwargs)
        
        # Evaluate weather response quality if query and response available
        if len(args) > 0 and result:
            query = str(args[0])
            response = str(result)
            
            # Run RAGAS evaluation for weather responses
            scores = observability.evaluate_response_quality(
                query=query,
                response=response,
                context=[response]  # Using response as context for basic evaluation
            )
            
            if scores:
                print(f"Weather response quality scores: {scores}")
        
        return result
    
    return wrapper