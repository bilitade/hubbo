"""LLM usage tracker with LangChain callbacks."""
from typing import Any, Dict, List, Optional
from datetime import datetime
from langchain.callbacks.base import BaseCallbackHandler
from sqlalchemy.orm import Session

from app.models.llm_log import LLMLog
from app.db.session import SessionLocal


class LLMUsageTracker(BaseCallbackHandler):
    """
    LangChain callback handler to track LLM usage.
    Automatically logs token usage, latency, and success/failure.
    """
    
    def __init__(
        self,
        user_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        feature: Optional[str] = None,
    ):
        """Initialize tracker with context."""
        self.user_id = user_id
        self.endpoint = endpoint
        self.feature = feature
        self.start_time = None
        self.prompt = None
        self.completion = None
        self.model = None
        self.provider = None
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0
        self.error_occurred = False
        self.error_message = None
        
    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        **kwargs: Any
    ) -> None:
        """Called when LLM starts running."""
        self.start_time = datetime.utcnow()
        self.prompt = prompts[0] if prompts else None
        
        # Extract model info
        if "model_name" in kwargs:
            self.model = kwargs["model_name"]
        elif "name" in serialized:
            self.model = serialized["name"]
        
        # Determine provider from model name
        if self.model:
            if "gpt" in self.model.lower():
                self.provider = "openai"
            elif "claude" in self.model.lower():
                self.provider = "anthropic"
            elif "gemini" in self.model.lower():
                self.provider = "google"
            else:
                self.provider = "unknown"
    
    def on_llm_end(
        self,
        response: Any,
        **kwargs: Any
    ) -> None:
        """Called when LLM ends running."""
        # Extract completion
        if hasattr(response, "generations") and response.generations:
            if response.generations[0]:
                self.completion = response.generations[0][0].text
        
        # Extract token usage
        if hasattr(response, "llm_output") and response.llm_output:
            token_usage = response.llm_output.get("token_usage", {})
            self.prompt_tokens = token_usage.get("prompt_tokens", 0)
            self.completion_tokens = token_usage.get("completion_tokens", 0)
            self.total_tokens = token_usage.get("total_tokens", 0)
        
        # Calculate latency
        latency_ms = None
        if self.start_time:
            latency_ms = int((datetime.utcnow() - self.start_time).total_seconds() * 1000)
        
        # Estimate cost
        estimated_cost = self._estimate_cost()
        
        # Log to database
        self._save_log(
            latency_ms=latency_ms,
            estimated_cost=estimated_cost,
            success=True,
        )
    
    def on_llm_error(
        self,
        error: Exception,
        **kwargs: Any
    ) -> None:
        """Called when LLM encounters an error."""
        self.error_occurred = True
        self.error_message = str(error)
        
        # Calculate latency
        latency_ms = None
        if self.start_time:
            latency_ms = int((datetime.utcnow() - self.start_time).total_seconds() * 1000)
        
        # Log error to database
        self._save_log(
            latency_ms=latency_ms,
            success=False,
            error_message=self.error_message,
            error_type=type(error).__name__,
        )
    
    def _estimate_cost(self) -> float:
        """Estimate API cost based on token usage."""
        # Pricing per 1K tokens (approximate, update as needed)
        pricing = {
            "gpt-4": {"prompt": 0.03, "completion": 0.06},
            "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
            "gpt-3.5-turbo": {"prompt": 0.0015, "completion": 0.002},
            "claude-3-opus": {"prompt": 0.015, "completion": 0.075},
            "claude-3-sonnet": {"prompt": 0.003, "completion": 0.015},
            "claude-3-haiku": {"prompt": 0.00025, "completion": 0.00125},
        }
        
        if not self.model or self.model not in pricing:
            return 0.0
        
        model_pricing = pricing[self.model]
        prompt_cost = (self.prompt_tokens / 1000) * model_pricing["prompt"]
        completion_cost = (self.completion_tokens / 1000) * model_pricing["completion"]
        
        return round(prompt_cost + completion_cost, 6)
    
    def _save_log(
        self,
        latency_ms: Optional[int],
        estimated_cost: Optional[float] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        error_type: Optional[str] = None,
    ):
        """Save log entry to database."""
        db: Session = SessionLocal()
        
        try:
            log_entry = LLMLog(
                user_id=self.user_id,
                provider=self.provider or "unknown",
                model=self.model or "unknown",
                prompt=self.prompt,
                prompt_tokens=self.prompt_tokens,
                completion=self.completion,
                completion_tokens=self.completion_tokens,
                total_tokens=self.total_tokens,
                latency_ms=latency_ms,
                success=success,
                error_message=error_message,
                error_type=error_type,
                estimated_cost=estimated_cost,
                endpoint=self.endpoint,
                feature=self.feature,
            )
            
            db.add(log_entry)
            db.commit()
        except Exception as e:
            print(f"Failed to save LLM log: {e}")
            db.rollback()
        finally:
            db.close()


def get_llm_tracker(
    user_id: Optional[str] = None,
    endpoint: Optional[str] = None,
    feature: Optional[str] = None,
) -> LLMUsageTracker:
    """
    Get an LLM usage tracker instance.
    Use this in LangChain calls to automatically track usage.
    
    Example:
        tracker = get_llm_tracker(user_id=user.id, feature="chat")
        llm = ChatOpenAI(callbacks=[tracker])
        response = llm.invoke("Hello!")
    """
    return LLMUsageTracker(
        user_id=user_id,
        endpoint=endpoint,
        feature=feature,
    )

