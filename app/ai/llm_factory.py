"""LLM factory for multi-provider support."""
from typing import Optional, List
from uuid import UUID
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.callbacks.base import BaseCallbackHandler
from app.ai.config import LLMProvider, LLMConfig
from app.ai.llm_callback import HubboLLMCallbackHandler
from app.config import settings


class LLMFactory:
    """Create LLM instances for any provider."""
    
    @staticmethod
    def create_llm(
        config: Optional[LLMConfig] = None,
        user_id: Optional[UUID] = None,
        endpoint: Optional[str] = None,
        feature: Optional[str] = None,
        extra_callbacks: Optional[List[BaseCallbackHandler]] = None
    ) -> BaseChatModel:
        """
        Create LLM with automatic usage tracking via callbacks.
        
        Args:
            config: Optional LLM configuration
            user_id: User ID for tracking (optional)
            endpoint: API endpoint name for tracking
            feature: Feature name for tracking
            extra_callbacks: Additional callbacks to include
            
        Returns:
            LLM instance with automatic logging enabled
        """
        if config is None:
            config = LLMConfig(
                provider=LLMProvider(settings.AI_PROVIDER),
                model=settings.AI_MODEL,
                temperature=settings.AI_TEMPERATURE,
                max_tokens=settings.AI_MAX_TOKENS,
                api_key=settings.OPENAI_API_KEY or settings.ANTHROPIC_API_KEY
            )
        
        # Create callbacks list with automatic tracking
        callbacks = []
        
        # Add Hubbo tracking callback (AUTOMATIC logging!)
        # Pass provider and model hints for better tracking
        hubbo_callback = HubboLLMCallbackHandler(
            user_id=user_id,
            endpoint=endpoint,
            feature=feature,
            provider=config.provider.value,
            model=config.model
        )
        callbacks.append(hubbo_callback)
        
        # Add any extra callbacks
        if extra_callbacks:
            callbacks.extend(extra_callbacks)
        
        if config.provider == LLMProvider.OPENAI:
            return ChatOpenAI(
                model=config.model,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                api_key=config.api_key or settings.OPENAI_API_KEY,
                callbacks=callbacks,  # ✨ Automatic LLM tracking!
            )
        
        elif config.provider == LLMProvider.ANTHROPIC:
            return ChatAnthropic(
                model=config.model,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                api_key=config.api_key or settings.ANTHROPIC_API_KEY,
                callbacks=callbacks,  # ✨ Automatic LLM tracking!
            )
        
        else:
            raise ValueError(f"Unsupported provider: {config.provider}")
    
    @staticmethod
    def get_models(provider: str) -> list[str]:
        """Get available models for provider."""
        from app.ai.config import PROVIDER_MODELS
        return PROVIDER_MODELS.get(provider, [])

