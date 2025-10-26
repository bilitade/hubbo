"""
LangChain Callback Handler for automatic LLM usage tracking.

This automatically logs ALL LLM calls without needing to modify each service.
"""
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from uuid import UUID, uuid4
import time

from langchain.callbacks.base import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from langchain_core.messages import BaseMessage

from app.models.llm_log import LLMLog
from app.db.session import SessionLocal


class HubboLLMCallbackHandler(BaseCallbackHandler):
    """
    Custom LangChain callback handler that automatically logs all LLM usage.
    
    This handler:
    - Tracks all LLM calls automatically
    - Captures tokens, costs, latency
    - Logs errors (API key, rate limits, etc.)
    - Works with any LLM provider (OpenAI, Anthropic, etc.)
    
    Usage:
        llm = ChatOpenAI(callbacks=[HubboLLMCallbackHandler(user_id=user.id)])
        # All calls are now automatically logged!
    """
    
    def __init__(
        self,
        user_id: Optional[UUID] = None,
        endpoint: Optional[str] = None,
        feature: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ):
        """Initialize the callback handler."""
        super().__init__(**kwargs)
        self.user_id = user_id
        self.endpoint = endpoint
        self.feature = feature
        self.start_time = None
        self.run_id = None
        self.prompt_text = None
        self.db = None
        self.provider_hint = provider  # Provider hint from factory
        self.model_hint = model  # Model hint from factory
    
    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Triggered when LLM starts."""
        self.start_time = time.time()
        self.run_id = run_id
        
        # Store prompt (combine if multiple)
        self.prompt_text = "\n\n".join(prompts) if prompts else ""
        
        print(f"🚀 LLM Call Started - Run ID: {run_id}")
        print(f"   Provider: {serialized.get('name', 'unknown')}")
        print(f"   Prompt length: {len(self.prompt_text)} chars")
    
    def on_chat_model_start(
        self,
        serialized: Dict[str, Any],
        messages: List[List[BaseMessage]],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Triggered when chat model starts."""
        self.start_time = time.time()
        self.run_id = run_id
        
        # Extract prompt from messages
        prompt_parts = []
        for message_list in messages:
            for msg in message_list:
                if hasattr(msg, 'content'):
                    prompt_parts.append(f"{msg.__class__.__name__}: {msg.content}")
        
        self.prompt_text = "\n".join(prompt_parts)
        
        print(f"🚀 Chat Model Started - Run ID: {run_id}")
        print(f"   Model: {serialized.get('name', 'unknown')}")
        print(f"   Messages: {len(messages[0]) if messages else 0}")
    
    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Triggered when LLM ends successfully."""
        latency_ms = int((time.time() - self.start_time) * 1000) if self.start_time else None
        
        # Extract response
        completion_text = ""
        if response.generations:
            for gen in response.generations[0]:
                if hasattr(gen, 'text'):
                    completion_text += gen.text
                elif hasattr(gen, 'message'):
                    completion_text += str(gen.message.content)
                else:
                    completion_text += str(gen)
        
        # Debug: Print full response structure
        print(f"🔍 DEBUG - LLM Response Structure:")
        print(f"   llm_output keys: {list(response.llm_output.keys()) if response.llm_output else 'None'}")
        
        # Extract token usage - try multiple locations
        llm_output = response.llm_output or {}
        token_usage = llm_output.get('token_usage', {})
        
        # Sometimes tokens are nested differently
        if not token_usage and 'usage' in llm_output:
            token_usage = llm_output['usage']
        
        # Debug token usage
        print(f"   token_usage: {token_usage}")
        
        # Try to get tokens from response metadata if available
        if hasattr(response, 'response_metadata'):
            print(f"   response_metadata: {response.response_metadata}")
            if 'token_usage' in response.response_metadata:
                token_usage = response.response_metadata['token_usage']
        
        # Also check generations for token info
        if response.generations and hasattr(response.generations[0][0], 'generation_info'):
            gen_info = response.generations[0][0].generation_info
            print(f"   generation_info: {gen_info}")
            if gen_info and 'token_usage' in gen_info:
                token_usage = gen_info['token_usage']
        
        prompt_tokens = token_usage.get('prompt_tokens') or token_usage.get('input_tokens')
        completion_tokens = token_usage.get('completion_tokens') or token_usage.get('output_tokens')
        total_tokens = token_usage.get('total_tokens')
        
        # Calculate total if not provided
        if not total_tokens and prompt_tokens and completion_tokens:
            total_tokens = prompt_tokens + completion_tokens
        
        # Extract model info - try multiple sources
        model_name = (
            llm_output.get('model_name') or 
            llm_output.get('model') or 
            self.model_hint or
            'unknown'
        )
        
        # Determine provider
        provider = self.provider_hint or self._determine_provider(model_name)
        
        print(f"   Extracted: provider={provider}, model={model_name}, tokens={total_tokens}")
        
        # Estimate cost
        estimated_cost = self._estimate_cost(
            provider,
            model_name,
            prompt_tokens or 0,
            completion_tokens or 0
        )
        
        print(f"✅ LLM Call Completed - Run ID: {run_id}")
        print(f"   Tokens: {total_tokens} ({prompt_tokens} + {completion_tokens})")
        print(f"   Latency: {latency_ms}ms")
        print(f"   Cost: ${estimated_cost:.6f}")
        
        # Save to database
        self._save_log(
            provider=provider,
            model=model_name,
            prompt=self.prompt_text,
            completion=completion_text,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            estimated_cost=estimated_cost,
            success=True,
            llm_output=llm_output
        )
    
    def on_llm_error(
        self,
        error: Union[Exception, KeyboardInterrupt],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Triggered when LLM encounters an error."""
        latency_ms = int((time.time() - self.start_time) * 1000) if self.start_time else None
        
        # Classify error type
        error_type = type(error).__name__
        error_message = str(error)
        
        # Determine specific error categories
        if "api_key" in error_message.lower() or "authentication" in error_message.lower():
            error_category = "API_KEY_ERROR"
        elif "rate_limit" in error_message.lower() or "quota" in error_message.lower():
            error_category = "RATE_LIMIT_EXCEEDED"
        elif "timeout" in error_message.lower():
            error_category = "TIMEOUT"
        elif "invalid" in error_message.lower() and "request" in error_message.lower():
            error_category = "INVALID_REQUEST"
        elif "model" in error_message.lower() and "not found" in error_message.lower():
            error_category = "MODEL_NOT_FOUND"
        else:
            error_category = "UNKNOWN_ERROR"
        
        print(f"❌ LLM Error - Run ID: {run_id}")
        print(f"   Error Type: {error_type}")
        print(f"   Category: {error_category}")
        print(f"   Message: {error_message[:200]}")
        print(f"   Latency: {latency_ms}ms")
        
        # Try to determine provider/model
        provider = "unknown"
        model = "unknown"
        
        # Save error to database
        self._save_log(
            provider=provider,
            model=model,
            prompt=self.prompt_text,
            completion=None,
            prompt_tokens=None,
            completion_tokens=None,
            total_tokens=None,
            latency_ms=latency_ms,
            estimated_cost=0.0,
            success=False,
            error_message=error_message,
            error_type=error_type,
            error_category=error_category
        )
    
    def _determine_provider(self, model_name: str) -> str:
        """Determine provider from model name."""
        model_lower = model_name.lower()
        
        if 'gpt' in model_lower or 'openai' in model_lower:
            return 'openai'
        elif 'claude' in model_lower or 'anthropic' in model_lower:
            return 'anthropic'
        else:
            return 'unknown'
    
    def _estimate_cost(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """Estimate cost based on provider and model."""
        # Pricing per 1K tokens (input, output)
        pricing = {
            "openai": {
                "gpt-4": (0.03, 0.06),
                "gpt-4-turbo": (0.01, 0.03),
                "gpt-4-turbo-preview": (0.01, 0.03),
                "gpt-3.5-turbo": (0.0005, 0.0015),
                "gpt-3.5-turbo-16k": (0.003, 0.004),
            },
            "anthropic": {
                "claude-3-opus": (0.015, 0.075),
                "claude-3-sonnet": (0.003, 0.015),
                "claude-3-haiku": (0.00025, 0.00125),
                "claude-2.1": (0.008, 0.024),
            }
        }
        
        # Get pricing for this model
        provider_pricing = pricing.get(provider, {})
        model_pricing = None
        
        # Try exact match first
        if model in provider_pricing:
            model_pricing = provider_pricing[model]
        else:
            # Try partial match
            for key in provider_pricing:
                if model.startswith(key):
                    model_pricing = provider_pricing[key]
                    break
        
        if not model_pricing:
            # Default to gpt-3.5-turbo pricing
            model_pricing = (0.0005, 0.0015)
        
        input_price_per_1k, output_price_per_1k = model_pricing
        
        # Calculate cost
        input_cost = (prompt_tokens / 1000) * input_price_per_1k
        output_cost = (completion_tokens / 1000) * output_price_per_1k
        
        return input_cost + output_cost
    
    def _save_log(
        self,
        provider: str,
        model: str,
        prompt: Optional[str],
        completion: Optional[str],
        prompt_tokens: Optional[int],
        completion_tokens: Optional[int],
        total_tokens: Optional[int],
        latency_ms: Optional[int],
        estimated_cost: float,
        success: bool,
        error_message: Optional[str] = None,
        error_type: Optional[str] = None,
        error_category: Optional[str] = None,
        llm_output: Optional[Dict] = None
    ) -> None:
        """Save log entry to database."""
        try:
            db = SessionLocal()
            
            # Prepare extra data
            extra_data = {}
            if error_category:
                extra_data['error_category'] = error_category
            if llm_output:
                # Include relevant llm_output fields
                if 'system_fingerprint' in llm_output:
                    extra_data['system_fingerprint'] = llm_output['system_fingerprint']
            
            log = LLMLog(
                user_id=self.user_id,
                provider=provider,
                model=model,
                prompt=prompt[:5000] if prompt else None,  # Truncate very long prompts
                prompt_tokens=prompt_tokens,
                completion=completion[:10000] if completion else None,  # Truncate long completions
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                latency_ms=latency_ms,
                success=success,
                error_message=error_message,
                error_type=error_type,
                estimated_cost=estimated_cost,
                endpoint=self.endpoint,
                feature=self.feature,
                extra_data=extra_data if extra_data else None
            )
            
            db.add(log)
            db.commit()
            
            print(f"💾 LLM Log saved to database - ID: {log.id}")
            
            db.close()
            
        except Exception as e:
            print(f"⚠️  Failed to save LLM log: {e}")
            import traceback
            traceback.print_exc()


def create_llm_callback(
    user_id: Optional[UUID] = None,
    endpoint: Optional[str] = None,
    feature: Optional[str] = None
) -> HubboLLMCallbackHandler:
    """
    Create a callback handler for LLM tracking.
    
    Usage:
        callback = create_llm_callback(user_id=user.id, feature="chat")
        llm = ChatOpenAI(callbacks=[callback])
        response = llm.invoke("Hello!")
        # Automatically logged!
    """
    return HubboLLMCallbackHandler(
        user_id=user_id,
        endpoint=endpoint,
        feature=feature
    )

