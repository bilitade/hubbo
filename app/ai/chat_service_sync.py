"""Dedicated chat service - synchronous version."""
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
import uuid
import asyncio

from app.ai.llm_factory import LLMFactory
from app.ai.config import LLMConfig
from app.ai.tools import create_tools
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.models.chat import Chat, ChatThread, ChatMessage
from app.models.user import User


class ChatContextBuilder:
    """Build context for chat conversations."""
    
    @staticmethod
    def build_project_context(db: Session, project_id: uuid.UUID) -> Dict[str, Any]:
        """Build context from project data."""
        from app.models.project import Project
        from app.models.task import Task
        from sqlalchemy import func
        
        # Get project
        project = db.query(Project).filter(Project.id == project_id).first()
        
        if not project:
            return {}
        
        # Get task statistics
        task_stats = db.query(
            Task.status,
            func.count(Task.id).label('count')
        ).filter(
            Task.project_id == project_id
        ).group_by(Task.status).all()
        
        stats_dict = {row.status: row.count for row in task_stats}
        
        return {
            "project_title": project.title,
            "project_status": project.status,
            "project_description": project.description or "No description",
            "tasks_total": sum(stats_dict.values()),
            "tasks_in_progress": stats_dict.get("in_progress", 0),
            "tasks_done": stats_dict.get("done", 0),
            "tasks_unassigned": stats_dict.get("unassigned", 0),
        }
    
    @staticmethod
    def build_task_context(db: Session, task_id: uuid.UUID) -> Dict[str, Any]:
        """Build context from task data."""
        from app.models.task import Task
        
        task = db.query(Task).filter(Task.id == task_id).first()
        
        if not task:
            return {}
        
        return {
            "task_title": task.title,
            "task_status": task.status,
            "task_description": task.description or "No description",
            "task_due_date": str(task.due_date) if task.due_date else "Not set",
        }
    
    @staticmethod
    def build_user_context(user: User) -> Dict[str, Any]:
        """Build context from user data."""
        # Get role names from user's roles
        role_names = [role.name for role in user.roles] if user.roles else []
        user_role = ", ".join(role_names) if role_names else (user.position or "User")
        
        return {
            "user_name": f"{user.first_name} {user.last_name}",
            "user_role": user_role,
            "user_email": user.email,
            "user_position": user.position or "Not set",
            "user_department": user.department or "Not set",
        }


class ChatService:
    """Service for managing AI chat conversations - synchronous version."""
    
    def __init__(self, llm_config: Optional[LLMConfig] = None):
        """Initialize chat service."""
        self.llm = LLMFactory.create_llm(llm_config)
    
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
        """Create a new chat thread."""
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
    
    def get_thread_messages(
        self,
        db: Session,
        thread_id: uuid.UUID,
        limit: Optional[int] = None
    ) -> List[ChatMessage]:
        """Get messages from a thread."""
        query = db.query(ChatMessage).filter(
            ChatMessage.thread_id == thread_id
        ).order_by(ChatMessage.created_at.asc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def add_message(
        self,
        db: Session,
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
        thread = db.query(ChatThread).filter(ChatThread.id == thread_id).first()
        thread.message_count += 1
        thread.updated_at = datetime.utcnow()
        
        # Update chat last_message_at
        chat = db.query(Chat).filter(Chat.id == thread.chat_id).first()
        chat.last_message_at = datetime.utcnow()
        chat.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(message)
        return message
    
    def chat_completion(
        self,
        db: Session,
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
        thread = db.query(ChatThread).filter(ChatThread.id == thread_id).first()
        
        # Build context
        context: Dict[str, Any] = {}
        
        # Add user context
        user_context = ChatContextBuilder.build_user_context(user)
        context.update(user_context)
        
        # Add project context if requested
        if include_project_context and project_id:
            project_context = ChatContextBuilder.build_project_context(db, project_id)
            context.update(project_context)
        
        # Add task context if requested
        if include_task_context and task_id:
            task_context = ChatContextBuilder.build_task_context(db, task_id)
            context.update(task_context)
        
        # Merge with thread context
        if thread.context:
            context.update(thread.context)
        
        # Get conversation history
        history_messages = self.get_thread_messages(db, thread_id)
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in history_messages
        ]
        
        # Use agent with tools
        try:
            print(f"🤖 Using agent with tools for: {user_message[:50]}...")
            
            # Create agent executor
            tools = create_tools(db)
            
            system_prompt = """You are Hubbo AI, an intelligent assistant for the Hubbo project management system.

You have access to tools that can:
- Search documents in Knowledge Base (search_knowledge_base)
- Search for specific projects (search_project)
- List all projects (get_projects)
- List tasks (get_tasks)
- Get project statistics (get_project_stats)
- Analyze team workload (get_user_workload)
- List ideas (get_ideas)
- Find overdue projects (get_overdue_projects)

Use these tools to provide accurate answers. Always format responses with markdown."""

            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                MessagesPlaceholder(variable_name="chat_history", optional=True),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])
            
            agent = create_openai_tools_agent(self.llm, tools, prompt)
            agent_executor = AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=True,
                max_iterations=10,
                handle_parsing_errors=True,
            )
            
            # Convert history to messages
            history_msgs = []
            for msg in history:
                if msg["role"] == "user":
                    history_msgs.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    history_msgs.append(AIMessage(content=msg["content"]))
            
            result = agent_executor.invoke({
                "input": user_message,
                "chat_history": history_msgs,
            })
            
            assistant_response = result.get("output", "I apologize, I couldn't process that.")
            print(f"✅ Agent response: {len(assistant_response)} chars")
        except Exception as e:
            print(f"Agent failed, falling back to simple chat: {e}")
            # Fallback to simple LLM if agent fails
            messages: List[BaseMessage] = []
            system_prompt = thread.system_prompt or self._get_default_system_prompt()
            messages.append(SystemMessage(content=system_prompt))
            
            if context:
                context_str = self._format_context(context)
                messages.append(SystemMessage(content=f"Current Context:\n{context_str}"))
            
            for msg in history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
            
            messages.append(HumanMessage(content=user_message))
            
            import asyncio
            response = asyncio.run(self.llm.ainvoke(messages))
            assistant_response = response.content
        
        # Save user message
        user_msg = self.add_message(
            db=db,
            thread_id=thread_id,
            role="user",
            content=user_message,
            user_id=user_id
        )
        
        # Save assistant message
        assistant_msg = self.add_message(
            db=db,
            thread_id=thread_id,
            role="assistant",
            content=assistant_response,
            model=model_name
        )
        
        return user_msg, assistant_msg
    
    def _get_default_system_prompt(self) -> str:
        """Get default system prompt for the chat assistant."""
        return """You are Hubbo AI, an intelligent AI assistant for the Hubbo project management system.

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
    
    def get_user_chats(
        self,
        db: Session,
        user_id: uuid.UUID,
        include_archived: bool = False,
        limit: int = 50
    ) -> List[Chat]:
        """Get all chats for a user."""
        query = db.query(Chat).filter(Chat.user_id == user_id)
        
        if not include_archived:
            query = query.filter(Chat.is_archived == False)
        
        query = query.order_by(desc(Chat.is_pinned), desc(Chat.updated_at)).limit(limit)
        
        return query.all()
    
    def get_chat_threads(
        self,
        db: Session,
        chat_id: uuid.UUID,
        include_inactive: bool = False
    ) -> List[ChatThread]:
        """Get all threads for a chat."""
        query = db.query(ChatThread).filter(ChatThread.chat_id == chat_id)
        
        if not include_inactive:
            query = query.filter(ChatThread.is_active == True)
        
        query = query.order_by(desc(ChatThread.updated_at))
        
        return query.all()

