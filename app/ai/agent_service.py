"""Agentic AI service using LangChain agents and tools."""
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import uuid

from app.ai.llm_factory import LLMFactory
from app.ai.config import LLMConfig
from app.ai.tools import create_tools
from app.ai.kb_service import KBService
from app.models.user import User


class AgentService:
    """Service for agentic AI with tool usage."""
    
    def __init__(self, llm_config: Optional[LLMConfig] = None):
        """Initialize agent service."""
        self.llm = LLMFactory.create_llm(llm_config)
    
    def _create_agent_prompt(self, has_kb_context: bool = False) -> ChatPromptTemplate:
        """Create the agent prompt template."""
        # Build system message parts
        system_parts = [
            "You are Hubbo AI, an intelligent assistant for the Hubbo project management system.",
            "",
            "You have access to tools that can fetch real-time information about:",
            "- Projects: their status, progress, deadlines, and details",
            "- Tasks: assignments, completion status, and workload",
            "- Ideas: brainstorming and innovation tracking",
            "- Team members: workload distribution and assignments",
            "- Statistics: overall system metrics and summaries",
            "- Knowledge Base: User-uploaded documents and company knowledge",
            "",
        ]
        
        # Add KB context section if needed
        if has_kb_context:
            system_parts.extend([
                "**KNOWLEDGE BASE CONTEXT**",
                "You have access to relevant information from the user's knowledge base:",
                "",
                "{kb_context}",
                "",
                "Use this information to provide more accurate and contextual answers. Always cite which document the information comes from when relevant.",
                "",
            ])
        
        system_parts.extend([
            "Your role is to:",
            "1. Understand user questions about their projects and tasks",
            "2. Use the appropriate tools to fetch accurate, real-time data",
            "3. Provide clear, helpful answers based on the actual data",
            "4. Offer insights and actionable recommendations",
            "5. Be concise but thorough in your responses",
            "",
            "**IMPORTANT - ALWAYS USE MARKDOWN FORMATTING:**",
            "",
            "1. **Headers**: Use ## for main sections, ### for subsections",
            "2. **Lists**: Use - or * for bullet points, 1. 2. 3. for numbered lists",
            "3. **Emphasis**: Use **bold** for important items, *italics* for notes",
            "4. **Tables**: Use markdown tables for data comparison",
            "5. **Code blocks**: Use `backticks` for IDs, names, or status values",
            "6. **Separators**: Use --- for visual breaks when appropriate",
            "7. **Emojis**: Use relevant emojis for visual appeal (✅ ❌ 📊 ⏰ 👥 etc.)",
            "",
            "**Response Structure Guidelines:**",
            "",
            "For project/task lists:",
            "```",
            "## Project Status",
            "",
            "**Total Projects**: 5",
            "",
            "### In Progress (2)",
            "- **Project Alpha** - Due: Jan 30 ⏰",
            "- **Project Beta** - Due: Feb 15 ✅",
            "",
            "### Planning (3)",
            "- Project Gamma",
            "- Project Delta",
            "```",
            "",
            "For statistics:",
            "```",
            "## Summary",
            "",
            "📊 **Projects**: 5 total",
            "- ✅ Done: 2",
            "- 🔄 In Progress: 2",
            "- 📋 Planning: 1",
            "```",
            "",
            "For issues/alerts:",
            "```",
            "## ⚠️ Attention Required",
            "",
            "❌ **Overdue Projects**: 2",
            "1. **Project X** - 3 days overdue",
            "2. **Project Y** - 7 days overdue",
            "```",
            "",
            "For workload:",
            "```",
            "## 👥 Team Workload",
            "",
            "| Team Member | Total Tasks | In Progress | Completed |",
            "|------------|-------------|-------------|-----------|",
            "| Sarah Johnson | 8 | 5 | 3 |",
            "| Mike Chen | 6 | 4 | 2 |",
            "```",
            "",
            "Always format your responses using markdown for maximum readability and visual appeal.",
        ])
        
        system_message = "\n".join(system_parts)
        
        # Create prompt with proper placeholders
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        return prompt
    
    def create_agent(self, db: Session, has_kb_context: bool = False) -> AgentExecutor:
        """Create an agent with tools."""
        tools = create_tools(db)
        prompt = self._create_agent_prompt(has_kb_context=has_kb_context)
        
        # Create the agent
        agent = create_openai_tools_agent(self.llm, tools, prompt)
        
        # Create agent executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=5,
            handle_parsing_errors=True,
        )
        
        return agent_executor
    
    async def chat_with_agent(
        self,
        db: Session,
        user_message: str,
        user: User,
        chat_history: Optional[List[Dict[str, str]]] = None,
        use_rag: bool = True
    ) -> str:
        """
        Chat with the agent using tools and RAG.
        
        Args:
            db: Database session
            user_message: User's question/message
            user: Current user
            chat_history: Previous conversation history
            use_rag: Whether to use RAG (Knowledge Base search)
            
        Returns:
            Agent's response
        """
        # Get KB context if RAG is enabled
        kb_context = ""
        has_kb_context = False
        
        if use_rag:
            try:
                kb_service = KBService(db)
                kb_context = await kb_service.get_context_for_query(
                    query=user_message,
                    k=3,
                    user_id=user.id
                )
                has_kb_context = bool(kb_context)
            except Exception as e:
                print(f"Error fetching KB context: {e}")
        
        # Create agent
        agent_executor = self.create_agent(db, has_kb_context=has_kb_context)
        
        # Build user context (not used in prompt anymore - removed to avoid error)
        role_names = [role.name for role in user.roles] if user.roles else []
        user_role = ", ".join(role_names) if role_names else (user.position or "User")
        
        # Convert chat history to messages
        history_messages = []
        if chat_history:
            for msg in chat_history[-10:]:  # Last 10 messages for context
                role = msg.get("role")
                content = msg.get("content")
                
                if role == "user":
                    history_messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    history_messages.append(AIMessage(content=content))
        
        # Execute agent
        try:
            invoke_input = {
                "input": user_message,
                "chat_history": history_messages,
            }
            
            # Add KB context if available
            if has_kb_context:
                invoke_input["kb_context"] = kb_context
            
            result = agent_executor.invoke(invoke_input)
            
            return result.get("output", "I'm sorry, I couldn't process that request.")
        
        except Exception as e:
            print(f"Agent error: {e}")
            return f"I encountered an issue while processing your request. Please try rephrasing your question."
    
    async def quick_answer(
        self,
        db: Session,
        question: str,
        user: User,
        use_rag: bool = True
    ) -> str:
        """
        Quick answer without conversation history.
        
        Args:
            db: Database session
            question: User's question
            user: Current user
            use_rag: Whether to use RAG
            
        Returns:
            Agent's response
        """
        return await self.chat_with_agent(db, question, user, chat_history=None, use_rag=use_rag)

