"""AI endpoints - simple and efficient."""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.ai import (
    ChatRequest,
    ChatResponse,
    IdeaGenerationRequest,
    ContentEnhanceRequest,
    AutoFillRequest,
    DocumentSearchRequest,
    DocumentSearchResponse,
    AIResponse,
)
from app.ai.service import AIService
from app.ai.documents import DocumentSearch
from app.ai.llm_factory import LLMFactory
from app.core.dependencies import get_current_user
from app.models.user import User
from app.config import settings
from app.middleware.input_sanitizer import InputSanitizer

router = APIRouter()


def check_ai_configured() -> None:
    """Check if AI is properly configured."""
    if not settings.OPENAI_API_KEY and not settings.ANTHROPIC_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service not configured. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY."
        )


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
) -> Any:
    """Chat with AI assistant."""
    check_ai_configured()
    
    # Sanitize inputs
    message = InputSanitizer.sanitize_ai_prompt(request.message, "message")
    system_prompt = None
    if request.system_prompt:
        system_prompt = InputSanitizer.sanitize_ai_prompt(request.system_prompt, "system_prompt")
    
    ai = AIService()
    
    user_context = {
        "user": f"{current_user.first_name} {current_user.last_name}",
        "role": current_user.role_title or "User",
    }
    if request.context:
        user_context.update(InputSanitizer.sanitize_dict(request.context))
    
    response = await ai.chat(
        message=message,
        system_prompt=system_prompt,
        context=user_context
    )
    
    return {"response": response, "model": settings.AI_MODEL}


@router.post("/generate-idea", response_model=AIResponse)
async def generate_idea(
    request: IdeaGenerationRequest,
    current_user: User = Depends(get_current_user)
) -> Any:
    """Generate creative ideas on a topic."""
    check_ai_configured()
    
    # Sanitize inputs
    topic = InputSanitizer.sanitize_text(request.topic, max_length=500, field_name="topic")
    context = None
    if request.context:
        context = InputSanitizer.sanitize_ai_prompt(request.context, "context")
    
    ai = AIService()
    result = await ai.generate_ideas(
        topic=topic,
        context=context
    )
    
    return {"result": result, "model": settings.AI_MODEL}


@router.post("/enhance-content", response_model=AIResponse)
async def enhance_content(
    request: ContentEnhanceRequest,
    current_user: User = Depends(get_current_user)
) -> Any:
    """Enhance content: improve, expand, summarize, professional."""
    check_ai_configured()
    
    # Sanitize inputs
    content = InputSanitizer.sanitize_ai_prompt(request.content, "content")
    
    ai = AIService()
    result = await ai.enhance_content(
        content=content,
        instruction=request.enhancement_type
    )
    
    return {"result": result, "model": settings.AI_MODEL}


@router.post("/auto-fill", response_model=AIResponse)
async def auto_fill(
    request: AutoFillRequest,
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get smart auto-fill suggestions."""
    check_ai_configured()
    
    # Sanitize inputs
    field_name = InputSanitizer.sanitize_field_name(request.field_name)
    existing_data = InputSanitizer.sanitize_dict(request.existing_data)
    
    ai = AIService()
    result = await ai.auto_fill(
        field_name=field_name,
        existing_data=existing_data
    )
    
    return {"result": result, "model": settings.AI_MODEL}


@router.post("/search-documents", response_model=DocumentSearchResponse)
async def search_documents(
    request: DocumentSearchRequest,
    current_user: User = Depends(get_current_user)
) -> Any:
    """Search documents using semantic search."""
    check_ai_configured()
    
    # Sanitize inputs
    query = InputSanitizer.sanitize_text(request.query, max_length=500, field_name="query")
    
    docs = DocumentSearch()
    results = await docs.search(query, k=request.max_results)
    
    formatted = [
        {
            "content": doc.page_content,
            "source": doc.metadata.get("source", "unknown")
        }
        for doc in results
    ]
    
    return {"results": formatted, "count": len(formatted)}


@router.get("/models")
async def list_models(current_user: User = Depends(get_current_user)) -> Any:
    """List available AI models."""
    models = LLMFactory.get_models(settings.AI_PROVIDER)
    
    return {
        "provider": settings.AI_PROVIDER,
        "current": settings.AI_MODEL,
        "available": models
    }

