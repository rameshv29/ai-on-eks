"""Observability wrapper for MCP server tools."""

import time
from functools import wraps
from typing import Any, Dict

# Import from parent directory
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

try:
    from observability import observability, trace_tool_call
except ImportError:
    # Fallback if observability not available
    def trace_tool_call(tool_name: str):
        def decorator(func):
            return func
        return decorator
    
    class MockObservability:
        def trace_tool_call(self, *args, **kwargs):
            pass
    
    observability = MockObservability()


def trace_mcp_tool(tool_name: str):
    """Decorator to trace MCP tool execution with observability."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Trace successful tool call
                observability.trace_tool_call(
                    tool_name=tool_name,
                    input_data={"args": str(args), "kwargs": str(kwargs)},
                    output_data={"result": str(result)[:500]},  # Truncate for logging
                    execution_time=execution_time
                )
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                # Trace failed tool call
                observability.trace_tool_call(
                    tool_name=tool_name,
                    input_data={"args": str(args), "kwargs": str(kwargs)},
                    output_data={"error": str(e)},
                    execution_time=execution_time
                )
                
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Trace successful tool call
                observability.trace_tool_call(
                    tool_name=tool_name,
                    input_data={"args": str(args), "kwargs": str(kwargs)},
                    output_data={"result": str(result)[:500]},  # Truncate for logging
                    execution_time=execution_time
                )
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                # Trace failed tool call
                observability.trace_tool_call(
                    tool_name=tool_name,
                    input_data={"args": str(args), "kwargs": str(kwargs)},
                    output_data={"error": str(e)},
                    execution_time=execution_time
                )
                
                raise
        
        # Return appropriate wrapper based on function type
        import asyncio
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator