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
from app.models.user import User


class AgentService:
    """Service for agentic AI with tool usage."""
    
    def __init__(self, llm_config: Optional[LLMConfig] = None):
        """Initialize agent service."""
        self.llm = LLMFactory.create_llm(llm_config)
    
    def _create_agent_prompt(self) -> ChatPromptTemplate:
        """Create the agent prompt template."""
        system_message = """You are Hubbo AI, an intelligent assistant for the Hubbo project management system.

You have access to tools that can fetch real-time information about:
- Projects: their status, progress, deadlines, and details
- Tasks: assignments, completion status, and workload
- Ideas: brainstorming and innovation tracking
- Team members: workload distribution and assignments
- Statistics: overall system metrics and summaries

Your role is to:
1. Understand user questions about their projects and tasks
2. Use the appropriate tools to fetch accurate, real-time data
3. Provide clear, helpful answers based on the actual data
4. Offer insights and actionable recommendations
5. Be concise but thorough in your responses

**IMPORTANT - ALWAYS USE MARKDOWN FORMATTING:**

1. **Headers**: Use ## for main sections, ### for subsections
2. **Lists**: Use - or * for bullet points, 1. 2. 3. for numbered lists
3. **Emphasis**: Use **bold** for important items, *italics* for notes
4. **Tables**: Use markdown tables for data comparison
5. **Code blocks**: Use `backticks` for IDs, names, or status values
6. **Separators**: Use --- for visual breaks when appropriate
7. **Emojis**: Use relevant emojis for visual appeal (✅ ❌ 📊 ⏰ 👥 etc.)

**Response Structure Guidelines:**

For project/task lists:
```
## Project Status

**Total Projects**: 5

### In Progress (2)
- **Project Alpha** - Due: Jan 30 ⏰
- **Project Beta** - Due: Feb 15 ✅

### Planning (3)
- Project Gamma
- Project Delta
```

For statistics:
```
## Summary

📊 **Projects**: 5 total
- ✅ Done: 2
- 🔄 In Progress: 2
- 📋 Planning: 1
```

For issues/alerts:
```
## ⚠️ Attention Required

❌ **Overdue Projects**: 2
1. **Project X** - 3 days overdue
2. **Project Y** - 7 days overdue
```

For workload:
```
## 👥 Team Workload

| Team Member | Total Tasks | In Progress | Completed |
|------------|-------------|-------------|-----------|
| Sarah Johnson | 8 | 5 | 3 |
| Mike Chen | 6 | 4 | 2 |
```

Always format your responses using markdown for maximum readability and visual appeal.

Current user context: {user_context}
"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        return prompt
    
    def create_agent(self, db: Session) -> AgentExecutor:
        """Create an agent with tools."""
        tools = create_tools(db)
        prompt = self._create_agent_prompt()
        
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
    
    def chat_with_agent(
        self,
        db: Session,
        user_message: str,
        user: User,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Chat with the agent using tools.
        
        Args:
            db: Database session
            user_message: User's question/message
            user: Current user
            chat_history: Previous conversation history
            
        Returns:
            Agent's response
        """
        # Create agent
        agent_executor = self.create_agent(db)
        
        # Build user context
        role_names = [role.name for role in user.roles] if user.roles else []
        user_role = ", ".join(role_names) if role_names else (user.position or "User")
        
        user_context = {
            "name": f"{user.first_name} {user.last_name}",
            "role": user_role,
            "position": user.position or "Not set",
        }
        
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
            result = agent_executor.invoke({
                "input": user_message,
                "user_context": str(user_context),
                "chat_history": history_messages,
            })
            
            return result.get("output", "I'm sorry, I couldn't process that request.")
        
        except Exception as e:
            print(f"Agent error: {e}")
            return f"I encountered an issue while processing your request. Please try rephrasing your question."
    
    def quick_answer(
        self,
        db: Session,
        question: str,
        user: User
    ) -> str:
        """
        Quick answer without conversation history.
        
        Args:
            db: Database session
            question: User's question
            user: Current user
            
        Returns:
            Agent's response
        """
        return self.chat_with_agent(db, question, user, chat_history=None)

