"""Observability module for Citymapper agent with Langfuse tracing and RAGAS evaluation."""

import os
import time
from typing import Dict, Any, Optional, List
from functools import wraps
import asyncio

try:
    from langfuse import Langfuse
    from ragas import evaluate
    from ragas.metrics import faithfulness, answer_relevancy, context_precision
    from ragas.llms import LangchainLLMWrapper
    from datasets import Dataset
    import boto3
    from langchain_aws import ChatBedrock
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False
    print("⚠️ Observability dependencies not fully available. Install with: pip install langfuse ragas datasets langchain-aws")


class ObservabilityManager:
    """Manages observability for multi-agent travel planning system."""
    
    def __init__(self):
        self.langfuse = None
        self.enabled = self._is_enabled()
        
        if self.enabled:
            self._initialize_langfuse()
    
    def _is_enabled(self) -> bool:
        """Check if observability is enabled via environment variables."""
        return (DEPENDENCIES_AVAILABLE and 
                bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY")))
    
    def _initialize_langfuse(self):
        """Initialize Langfuse client."""
        try:
            self.langfuse = Langfuse(
                public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
                secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
                host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
            )
            print("✅ Langfuse observability initialized")
        except Exception as e:
            print(f"⚠️ Langfuse initialization failed: {e}")
            self.enabled = False
    
    def trace_agent_request(self, agent_name: str, user_query: str, response: str, 
                           metadata: Optional[Dict] = None):
        """Trace agent request/response."""
        if not self.enabled:
            return
        
        try:
            trace = self.langfuse.trace(
                name=f"{agent_name}_request",
                input=user_query,
                output=response,
                metadata={
                    "agent": agent_name,
                    "timestamp": time.time(),
                    **(metadata or {})
                }
            )
            return trace
        except Exception as e:
            print(f"⚠️ Tracing failed: {e}")
    
    def trace_tool_call(self, tool_name: str, input_data: Dict, output_data: Dict,
                       execution_time: float, parent_trace=None):
        """Trace MCP tool calls."""
        if not self.enabled:
            return
        
        try:
            span = self.langfuse.span(
                name=f"tool_{tool_name}",
                input=input_data,
                output=output_data,
                metadata={
                    "tool": tool_name,
                    "execution_time_ms": execution_time * 1000,
                    "timestamp": time.time()
                }
            )
            if parent_trace:
                span.parent_observation_id = parent_trace.id
            return span
        except Exception as e:
            print(f"⚠️ Tool tracing failed: {e}")
    
    def trace_multi_agent_communication(self, from_agent: str, to_agent: str, 
                                      message: str, response: str):
        """Trace multi-agent communication."""
        if not self.enabled:
            return
        
        try:
            trace = self.langfuse.trace(
                name="multi_agent_communication",
                input={"from": from_agent, "message": message},
                output={"to": to_agent, "response": response},
                metadata={
                    "communication_type": "agent_to_agent",
                    "from_agent": from_agent,
                    "to_agent": to_agent,
                    "timestamp": time.time()
                }
            )
            return trace
        except Exception as e:
            print(f"⚠️ Multi-agent tracing failed: {e}")
    
    def evaluate_response_quality(self, query: str, response: str, context: List[str] = None):
        """Evaluate response quality using RAGAS metrics with Bedrock."""
        if not self.enabled:
            return {}
        
        try:
            # Initialize Bedrock LLM for RAGAS
            bedrock_llm = ChatBedrock(
                model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
                region_name=os.getenv("AWS_REGION", "us-west-2")
            )
            
            # Wrap for RAGAS
            ragas_llm = LangchainLLMWrapper(bedrock_llm)
            
            # Prepare dataset for RAGAS evaluation
            data = {
                "question": [query],
                "answer": [response],
                "contexts": [context or [response]],
                "ground_truth": [response]  # Using response as ground truth for basic evaluation
            }
            
            dataset = Dataset.from_dict(data)
            
            # Configure metrics with Bedrock LLM
            metrics = [faithfulness, answer_relevancy, context_precision]
            
            # Run RAGAS evaluation with Bedrock LLM
            from ragas.run_config import RunConfig
            
            run_config = RunConfig(
                max_workers=1,
                timeout=60
            )
            
            result = evaluate(
                dataset=dataset,
                metrics=metrics,
                llm=ragas_llm,
                run_config=run_config
            )
            
            scores = {
                "faithfulness": float(result["faithfulness"]),
                "answer_relevancy": float(result["answer_relevancy"]),
                "context_precision": float(result["context_precision"])
            }
            
            # Log to Langfuse
            if self.langfuse:
                self.langfuse.create_score(
                    name="ragas_evaluation",
                    value=sum(scores.values()) / len(scores),
                    comment=f"RAGAS evaluation with Bedrock: {scores}"
                )
            
            return scores
            
        except Exception as e:
            print(f"⚠️ RAGAS evaluation failed: {e}")
            return {}


# Global observability manager instance
observability = ObservabilityManager()


def trace_agent_call(agent_name: str):
    """Decorator to trace agent calls."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not observability.enabled:
                return await func(*args, **kwargs)
            
            start_time = time.time()
            user_query = str(args[0]) if args else str(kwargs.get('query', ''))
            
            try:
                response = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Trace the request
                observability.trace_agent_request(
                    agent_name=agent_name,
                    user_query=user_query,
                    response=str(response),
                    metadata={
                        "execution_time_ms": execution_time * 1000,
                        "success": True
                    }
                )
                
                return response
                
            except Exception as e:
                execution_time = time.time() - start_time
                observability.trace_agent_request(
                    agent_name=agent_name,
                    user_query=user_query,
                    response=f"Error: {str(e)}",
                    metadata={
                        "execution_time_ms": execution_time * 1000,
                        "success": False,
                        "error": str(e)
                    }
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not observability.enabled:
                return func(*args, **kwargs)
            
            start_time = time.time()
            user_query = str(args[0]) if args else str(kwargs.get('query', ''))
            
            try:
                response = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Trace the request
                observability.trace_agent_request(
                    agent_name=agent_name,
                    user_query=user_query,
                    response=str(response),
                    metadata={
                        "execution_time_ms": execution_time * 1000,
                        "success": True
                    }
                )
                
                return response
                
            except Exception as e:
                execution_time = time.time() - start_time
                observability.trace_agent_request(
                    agent_name=agent_name,
                    user_query=user_query,
                    response=f"Error: {str(e)}",
                    metadata={
                        "execution_time_ms": execution_time * 1000,
                        "success": False,
                        "error": str(e)
                    }
                )
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


def trace_tool_call(tool_name: str):
    """Decorator to trace MCP tool calls."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not observability.enabled:
                return func(*args, **kwargs)
            
            start_time = time.time()
            input_data = {"args": args, "kwargs": kwargs}
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                observability.trace_tool_call(
                    tool_name=tool_name,
                    input_data=input_data,
                    output_data={"result": str(result)},
                    execution_time=execution_time
                )
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                observability.trace_tool_call(
                    tool_name=tool_name,
                    input_data=input_data,
                    output_data={"error": str(e)},
                    execution_time=execution_time
                )
                raise
        
        return wrapper
    return decorator