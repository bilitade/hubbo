"""Dedicated chat service - separate from other AI services."""
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
import uuid

from app.ai.llm_factory import LLMFactory
from app.ai.config import LLMConfig
from app.models.chat import Chat, ChatThread, ChatMessage
from app.models.user import User


class ChatContextBuilder:
    """Build context for chat conversations."""
    
    @staticmethod
    async def build_project_context(db: AsyncSession, project_id: uuid.UUID) -> Dict[str, Any]:
        """Build context from project data."""
        from app.models.project import Project
        from app.models.task import Task
        from sqlalchemy import func
        
        # Get project
        result = await db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        
        if not project:
            return {}
        
        # Get task statistics
        task_result = await db.execute(
            select(
                Task.status,
                func.count(Task.id).label('count')
            ).where(
                Task.project_id == project_id
            ).group_by(Task.status)
        )
        task_stats = {row.status: row.count for row in task_result}
        
        return {
            "project_title": project.title,
            "project_status": project.status,
            "project_description": project.description or "No description",
            "tasks_total": sum(task_stats.values()),
            "tasks_in_progress": task_stats.get("in_progress", 0),
            "tasks_done": task_stats.get("done", 0),
            "tasks_unassigned": task_stats.get("unassigned", 0),
        }
    
    @staticmethod
    async def build_task_context(db: AsyncSession, task_id: uuid.UUID) -> Dict[str, Any]:
        """Build context from task data."""
        from app.models.task import Task
        
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        
        if not task:
            return {}
        
        return {
            "task_title": task.title,
            "task_status": task.status,
            "task_description": task.description or "No description",
            "task_due_date": str(task.due_date) if task.due_date else "Not set",
        }
    
    @staticmethod
    async def build_user_context(user: User) -> Dict[str, Any]:
        """Build context from user data."""
        return {
            "user_name": f"{user.first_name} {user.last_name}",
            "user_role": user.role_title or "User",
            "user_email": user.email,
        }


class ChatService:
    """Service for managing AI chat conversations."""
    
    def __init__(self, llm_config: Optional[LLMConfig] = None):
        """Initialize chat service."""
        self.llm = LLMFactory.create_llm(llm_config)
    
    async def create_chat(
        self,
        db: AsyncSession,
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
        await db.commit()
        await db.refresh(chat)
        return chat
    
    async def create_thread(
        self,
        db: AsyncSession,
        chat_id: uuid.UUID,
        title: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None
    ) -> ChatThread:
        """Create a new chat thread."""
        thread = ChatThread(
            chat_id=chat_id,
            title=title,
            context=context,
            system_prompt=system_prompt
        )
        db.add(thread)
        await db.commit()
        await db.refresh(thread)
        return thread
    
    async def get_thread_messages(
        self,
        db: AsyncSession,
        thread_id: uuid.UUID,
        limit: Optional[int] = None
    ) -> List[ChatMessage]:
        """Get messages from a thread."""
        query = select(ChatMessage).where(
            ChatMessage.thread_id == thread_id
        ).order_by(ChatMessage.created_at.asc())
        
        if limit:
            query = query.limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def add_message(
        self,
        db: AsyncSession,
        thread_id: uuid.UUID,
        role: str,
        content: str,
        user_id: Optional[uuid.UUID] = None,
        model: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> ChatMessage:
        """Add a message to a thread."""
        message = ChatMessage(
            thread_id=thread_id,
            role=role,
            content=content,
            user_id=user_id,
            model=model,
            extra_data=extra_data
        )
        db.add(message)
        
        # Update thread message count
        thread_result = await db.execute(
            select(ChatThread).where(ChatThread.id == thread_id)
        )
        thread = thread_result.scalar_one()
        thread.message_count += 1
        thread.updated_at = datetime.utcnow()
        
        # Update chat last_message_at
        chat_result = await db.execute(
            select(Chat).where(Chat.id == thread.chat_id)
        )
        chat = chat_result.scalar_one()
        chat.last_message_at = datetime.utcnow()
        chat.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(message)
        return message
    
    async def chat_completion(
        self,
        db: AsyncSession,
        thread_id: uuid.UUID,
        user_message: str,
        user_id: uuid.UUID,
        user: User,
        model_name: str = "gpt-3.5-turbo",
        include_project_context: bool = False,
        include_task_context: bool = False,
        project_id: Optional[uuid.UUID] = None,
        task_id: Optional[uuid.UUID] = None
    ) -> tuple[ChatMessage, ChatMessage]:
        """
        Process a chat message and get AI response.
        
        Returns:
            Tuple of (user_message, assistant_message)
        """
        # Get thread
        thread_result = await db.execute(
            select(ChatThread).where(ChatThread.id == thread_id)
        )
        thread = thread_result.scalar_one()
        
        # Build context
        context: Dict[str, Any] = {}
        
        # Add user context
        user_context = await ChatContextBuilder.build_user_context(user)
        context.update(user_context)
        
        # Add project context if requested
        if include_project_context and project_id:
            project_context = await ChatContextBuilder.build_project_context(db, project_id)
            context.update(project_context)
        
        # Add task context if requested
        if include_task_context and task_id:
            task_context = await ChatContextBuilder.build_task_context(db, task_id)
            context.update(task_context)
        
        # Merge with thread context
        if thread.context:
            context.update(thread.context)
        
        # Get conversation history
        history_messages = await self.get_thread_messages(db, thread_id)
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in history_messages
        ]
        
        # Build messages for LLM
        messages: List[BaseMessage] = []
        
        # System prompt
        system_prompt = thread.system_prompt or self._get_default_system_prompt()
        messages.append(SystemMessage(content=system_prompt))
        
        # Add context
        if context:
            context_str = self._format_context(context)
            messages.append(SystemMessage(content=f"Current Context:\n{context_str}"))
        
        # Add history
        for msg in history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        
        # Add current message
        messages.append(HumanMessage(content=user_message))
        
        # Get AI response
        response = await self.llm.ainvoke(messages)
        assistant_response = response.content
        
        # Save user message
        user_msg = await self.add_message(
            db=db,
            thread_id=thread_id,
            role="user",
            content=user_message,
            user_id=user_id
        )
        
        # Save assistant message
        assistant_msg = await self.add_message(
            db=db,
            thread_id=thread_id,
            role="assistant",
            content=assistant_response,
            model=model_name
        )
        
        return user_msg, assistant_msg
    
    def _get_default_system_prompt(self) -> str:
        """Get default system prompt for the chat assistant."""
        return """You are Guru, an intelligent AI assistant for the Hubbo project management system.

You have access to information about:
- Projects: status, descriptions, metrics, and progress
- Tasks: assignments, status, due dates, and completion
- Users: names, roles, and responsibilities
- Experiments: research and testing activities

Your role is to:
1. Answer questions about project status and progress
2. Provide insights on task completion and workload
3. Help users understand their projects better
4. Offer suggestions for improving productivity
5. Summarize information clearly and concisely

Be helpful, professional, and concise. When you don't have specific information, be honest about it."""
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context dictionary for LLM."""
        lines = []
        for key, value in context.items():
            # Make keys more readable
            readable_key = key.replace("_", " ").title()
            lines.append(f"- {readable_key}: {value}")
        return "\n".join(lines)
    
    async def get_user_chats(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        include_archived: bool = False,
        limit: int = 50
    ) -> List[Chat]:
        """Get all chats for a user."""
        query = select(Chat).where(Chat.user_id == user_id)
        
        if not include_archived:
            query = query.where(Chat.is_archived == False)
        
        query = query.order_by(desc(Chat.is_pinned), desc(Chat.updated_at)).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_chat_threads(
        self,
        db: AsyncSession,
        chat_id: uuid.UUID,
        include_inactive: bool = False
    ) -> List[ChatThread]:
        """Get all threads for a chat."""
        query = select(ChatThread).where(ChatThread.chat_id == chat_id)
        
        if not include_inactive:
            query = query.where(ChatThread.is_active == True)
        
        query = query.order_by(desc(ChatThread.updated_at))
        
        result = await db.execute(query)
        return list(result.scalars().all())

