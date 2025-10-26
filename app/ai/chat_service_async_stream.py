"""Async chat service with streaming support."""
from typing import Optional, Dict, Any, List, AsyncIterator
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
import uuid
import json

from app.ai.llm_factory import LLMFactory
from app.ai.config import LLMConfig
from app.ai.intelligent_agent import IntelligentAgent
from app.models.chat import Chat, ChatThread, ChatMessage
from app.models.user import User


class AsyncStreamingChatService:
    """Async chat service with streaming support for real-time responses."""
    
    def __init__(self, llm_config: Optional[LLMConfig] = None, user_id: Optional[uuid.UUID] = None):
        """Initialize chat service with automatic logging."""
        self.llm = LLMFactory.create_llm(
            config=llm_config,
            user_id=user_id,
            feature="streaming_chat"
        )
        self.agent = IntelligentAgent(llm_config, user_id=user_id)
    
    def create_chat(
        self,
        db: Session,
        user_id: uuid.UUID,
        title: str,
        description: Optional[str] = None
    ) -> Chat:
        """Create a new chat."""
        chat = Chat(
            user_id=user_id,
            title=title,
            description=description
        )
        db.add(chat)
        db.commit()
        db.refresh(chat)
        return chat
    
    def create_thread(
        self,
        db: Session,
        chat_id: uuid.UUID,
        title: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None
    ) -> ChatThread:
        """Create a new thread in a chat."""
        thread = ChatThread(
            chat_id=chat_id,
            title=title,
            context=context,
            system_prompt=system_prompt
        )
        db.add(thread)
        db.commit()
        db.refresh(thread)
        return thread
    
    def add_message(
        self,
        db: Session,
        thread_id: uuid.UUID,
        role: str,
        content: str,
        user_id: Optional[uuid.UUID] = None,
        model: Optional[str] = None
    ) -> ChatMessage:
        """Add a message to a thread."""
        message = ChatMessage(
            thread_id=thread_id,
            role=role,
            content=content,
            user_id=user_id,
            model=model
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message
    
    def get_thread_messages(
        self,
        db: Session,
        thread_id: uuid.UUID,
        limit: int = 100
    ) -> List[ChatMessage]:
        """Get messages from a thread."""
        stmt = select(ChatMessage).where(
            ChatMessage.thread_id == thread_id
        ).order_by(ChatMessage.created_at).limit(limit)
        
        return list(db.execute(stmt).scalars().all())
    
    async def stream_agent_response(
        self,
        db: Session,
        thread_id: uuid.UUID,
        user_message: str,
        user: User,
        model_name: str = "gpt-4"
    ) -> AsyncIterator[str]:
        """
        Stream agent response with typing animation.
        
        Yields chunks of text as they're generated.
        """
        # Get thread
        thread = db.query(ChatThread).filter(ChatThread.id == thread_id).first()
        if not thread:
            yield json.dumps({"error": "Thread not found"})
            return
        
        # Save user message
        user_msg = self.add_message(
            db=db,
            thread_id=thread_id,
            role="user",
            content=user_message,
            user_id=user.id
        )
        
        # Yield user message confirmation
        yield json.dumps({
            "type": "user_message",
            "message_id": str(user_msg.id),
            "content": user_message
        }) + "\n"
        
        # Get conversation history
        history_messages = self.get_thread_messages(db, thread_id)
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in history_messages[:-1]  # Exclude the message we just added
        ]
        
        # Stream agent response
        full_response = ""
        chunk_count = 0
        
        try:
            # Get agent response (streaming) - automatically logged via callback!
            async for chunk in self._stream_agent_with_tools(
                db=db,
                user_message=user_message,
                user=user,
                chat_history=history
            ):
                chunk_count += 1
                print(f"📨 Backend streaming chunk #{chunk_count}: '{chunk}'")
                full_response += chunk
                
                chunk_data = json.dumps({
                    "type": "content",
                    "chunk": chunk
                })
                print(f"📤 Sending: {chunk_data}")
                yield chunk_data + "\n"
        
        except Exception as e:
            print(f"❌ Error in streaming: {e}")
            import traceback
            traceback.print_exc()
            error_msg = f"Error: {str(e)}"
            yield json.dumps({
                "type": "error",
                "message": error_msg
            }) + "\n"
            full_response = error_msg
        
        print(f"✅ Streaming complete. Total chunks sent: {chunk_count}, Total length: {len(full_response)}")
        
        # Save assistant message
        assistant_msg = self.add_message(
            db=db,
            thread_id=thread_id,
            role="assistant",
            content=full_response,
            model=model_name
        )
        
        # Yield completion
        yield json.dumps({
            "type": "done",
            "message_id": str(assistant_msg.id),
            "total_length": len(full_response)
        }) + "\n"
    
    async def _stream_agent_with_tools(
        self,
        db: Session,
        user_message: str,
        user: User,
        chat_history: List[Dict[str, str]]
    ) -> AsyncIterator[str]:
        """Stream agent response using tools."""
        import asyncio
        
        print("🚀 Starting agent with tools...")
        print(f"📝 User message: {user_message}")
        
        try:
            # Get full response from agent (agents don't stream well with tools)
            response = await self.agent.chat(
                db=db,
                user=user,
                message=user_message,
                chat_history=chat_history
            )
            
            print(f"✅ Agent response received: {len(response)} chars")
            print(f"📄 Response preview: {response[:100]}...")
            
            # Stream the response word by word for typing effect
            words = response.split(' ')
            print(f"🔢 Splitting into {len(words)} words")
            
            for i, word in enumerate(words):
                if i > 0:
                    yield " "
                yield word
                # Small delay for typing effect (adjust for speed)
                await asyncio.sleep(0.03)  # 30ms between words
                
                if (i + 1) % 10 == 0:
                    print(f"📊 Progress: {i + 1}/{len(words)} words sent")
            
            print(f"✅ All {len(words)} words sent!")
            
        except Exception as e:
            print(f"❌ Error in agent execution: {e}")
            import traceback
            traceback.print_exc()
            yield f"Error: {str(e)}"
    
    async def stream_simple_chat(
        self,
        db: Session,
        thread_id: uuid.UUID,
        user_message: str,
        user_id: uuid.UUID,
        model_name: str = "gpt-4"
    ) -> AsyncIterator[str]:
        """
        Stream simple LLM response (no tools).
        
        Yields chunks of text as they're generated.
        """
        # Get thread
        thread = db.query(ChatThread).filter(ChatThread.id == thread_id).first()
        if not thread:
            yield json.dumps({"error": "Thread not found"})
            return
        
        # Save user message
        user_msg = self.add_message(
            db=db,
            thread_id=thread_id,
            role="user",
            content=user_message,
            user_id=user_id
        )
        
        yield json.dumps({
            "type": "user_message",
            "message_id": str(user_msg.id)
        }) + "\n"
        
        # Get conversation history
        history_messages = self.get_thread_messages(db, thread_id)
        
        # Build messages
        messages: List[BaseMessage] = []
        system_prompt = thread.system_prompt or self._get_default_system_prompt()
        messages.append(SystemMessage(content=system_prompt))
        
        # Add history
        for msg in history_messages[:-1]:  # Exclude the one we just added
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                messages.append(AIMessage(content=msg.content))
        
        messages.append(HumanMessage(content=user_message))
        
        # Stream response
        full_response = ""
        async for chunk in self.llm.astream(messages):
            content = chunk.content
            full_response += content
            yield json.dumps({
                "type": "content",
                "chunk": content
            }) + "\n"
        
        # Save assistant message
        assistant_msg = self.add_message(
            db=db,
            thread_id=thread_id,
            role="assistant",
            content=full_response,
            model=model_name
        )
        
        yield json.dumps({
            "type": "done",
            "message_id": str(assistant_msg.id)
        }) + "\n"
    
    def _get_default_system_prompt(self) -> str:
        """Get default system prompt."""
        return """You are Hubbo AI, an intelligent AI assistant for the Hubbo project management system.

You have access to information about:
- Projects: status, descriptions, metrics, and progress
- Tasks: assignments, status, due dates, and completion
- Ideas: brainstorming and innovation tracking
- Team members: roles, workload, and assignments
- Documents: uploaded files and company knowledge

Provide helpful, accurate, and well-formatted responses using markdown.
"""

