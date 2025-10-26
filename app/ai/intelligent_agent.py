"""
Multipurpose Intelligent Agent for Hubbo Platform.

A comprehensive AI agent that can:
- Answer questions about projects, tasks, ideas, and workflows
- Search and summarize documents from Knowledge Base
- Provide personalized responses based on user context
- Stream responses in real-time
- Maintain conversation history
- Use multiple tools seamlessly
"""
from typing import Optional, Dict, Any, List, AsyncIterator
from sqlalchemy.orm import Session
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from uuid import UUID

from app.ai.llm_factory import LLMFactory
from app.ai.config import LLMConfig
from app.ai.tools import create_tools
from app.models.user import User


class IntelligentAgent:
    """
    Multipurpose intelligent agent for the Hubbo platform.
    
    Features:
    - Multi-tool usage (projects, tasks, ideas, KB search)
    - Streaming responses
    - Chat history maintenance
    - User-personalized responses
    - Multi-user support with isolation
    """
    
    def __init__(self, llm_config: Optional[LLMConfig] = None):
        """Initialize intelligent agent."""
        self.llm = LLMFactory.create_llm(llm_config)
    
    def _create_system_prompt(self) -> str:
        """Create comprehensive system prompt."""
        return """You are Hubbo AI, an advanced intelligent assistant for the Hubbo project management and knowledge platform.

## 🎯 YOUR CAPABILITIES

You have access to powerful tools that can:

**1. Project Management:**
- `search_project`: Find specific projects by name (e.g., "Lumo MVP", "Website Redesign")
- `get_projects`: List all projects with filters (status, completion, etc.)
- `get_project_stats`: Get overall project statistics and health
- `get_overdue_projects`: Find projects behind schedule

**2. Task Management:**
- `get_tasks`: List tasks with filters (status, assignee, project)
- Task assignments, deadlines, and completion tracking

**3. Team & Workload:**
- `get_user_workload`: Analyze team workload distribution
- Who's working on what, capacity analysis

**4. Ideas & Innovation:**
- `get_ideas`: Browse brainstorming and innovation ideas

**5. Knowledge Base:**
- `search_knowledge_base`: Search uploaded documents (policies, specs, plans, etc.)
- Find information from PDFs, DOCX, and other uploaded files
- Provide answers with citations from documents

## 🧠 YOUR INTELLIGENCE

**Always:**
1. **Choose the right tool** - If asked about "Lumo MVP", check if it's a project OR document
2. **Use multiple tools** when needed - Combine project data + document search
3. **Cite sources** - When using KB, mention the document name
4. **Be proactive** - Offer insights and recommendations
5. **Stay accurate** - Only use data from tools, never make up information

**Examples:**

❓ *"What's the status of Lumo MVP?"*
→ Use `search_project` first, then `search_knowledge_base` if not found

❓ *"Who has the most tasks?"*
→ Use `get_user_workload` tool

❓ *"What does our vacation policy say?"*
→ Use `search_knowledge_base` to find policy documents

❓ *"Compare project Alpha with project specs in documents"*
→ Use `search_project` AND `search_knowledge_base`, then compare

## 📊 RESPONSE FORMATTING

**ALWAYS use markdown for beautiful, readable responses:**

### For Summaries:
```markdown
## 📋 Project Summary

**Name**: Project Alpha
**Status**: In Progress (65% complete)
**Owner**: Sarah Johnson

### Progress
- ✅ Completed: 13 tasks
- 🔄 In Progress: 7 tasks
- 📝 Total: 20 tasks

### Timeline
⏰ **Due**: March 30, 2025
```

### For Document Results:
```markdown
## 📄 From Documents

**[Source: hr_policy.pdf]**

According to the company policy, employees are entitled to 20 vacation days per year...

**Key Points:**
- Vacation days: 20 per year
- Rollover: Up to 5 days
- Notice: 2 weeks advance
```

### For Combined Queries:
```markdown
## 🔍 Analysis

### From Database:
**Project Lumo MVP**
- Status: In Progress
- Tasks: 15 total, 8 completed

### From Documents:
**[Source: lumo_requirements.pdf]**
The Lumo MVP requires AI features including...

### Comparison:
The project is 53% complete, which aligns with the Q1 2025 timeline mentioned in requirements.
```

## 💡 PERSONALIZATION

Current user: {user_name} ({user_role})

Tailor your responses to the user's role and needs. Be professional yet friendly.

## ⚠️ IMPORTANT RULES

1. **ALWAYS use tools** - Don't guess, use tools to get accurate data
2. **NEVER make up data** - If tools return no results, say so
3. **CITE sources** - Especially for document searches
4. **Use markdown** - Make responses beautiful and scannable
5. **Be concise** - But thorough when details are needed
6. **Offer next steps** - Suggest related actions when helpful

You are the brain of Hubbo. Be intelligent, helpful, and accurate!
"""
    
    def _create_agent_executor(
        self,
        db: Session,
        user: User
    ) -> AgentExecutor:
        """Create agent executor with tools and prompts."""
        # Get all tools
        tools = create_tools(db)
        
        # Create system prompt with user context
        system_prompt = self._create_system_prompt()
        
        # Build user context string
        role_names = [role.name for role in user.roles] if user.roles else []
        user_role = ", ".join(role_names) if role_names else (user.position or "Team Member")
        user_name = f"{user.first_name} {user.last_name}"
        
        # Replace user placeholders in system prompt
        system_prompt = system_prompt.replace("{user_name}", user_name)
        system_prompt = system_prompt.replace("{user_role}", user_role)
        
        # Create prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Create agent
        agent = create_openai_tools_agent(self.llm, tools, prompt)
        
        # Create executor with verbose mode for debugging
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=10,  # Allow multiple tool uses
            handle_parsing_errors=True,
            return_intermediate_steps=False,
        )
        
        return agent_executor
    
    async def chat(
        self,
        db: Session,
        user: User,
        message: str,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Standard chat (non-streaming).
        
        Args:
            db: Database session
            user: Current user
            message: User message
            chat_history: Previous conversation
            
        Returns:
            Agent response
        """
        agent_executor = self._create_agent_executor(db, user)
        
        # Convert chat history to messages
        history_messages = []
        if chat_history:
            for msg in chat_history[-10:]:  # Last 10 for context
                role = msg.get("role")
                content = msg.get("content")
                
                if role == "user":
                    history_messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    history_messages.append(AIMessage(content=content))
        
        try:
            result = agent_executor.invoke({
                "input": message,
                "chat_history": history_messages,
            })
            
            return result.get("output", "I apologize, I couldn't process that request.")
        
        except Exception as e:
            print(f"❌ Agent error: {e}")
            import traceback
            traceback.print_exc()
            return f"I encountered an error while processing your request. Please try rephrasing or ask something else."
    
    async def stream_chat(
        self,
        db: Session,
        user: User,
        message: str,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> AsyncIterator[str]:
        """
        Stream chat response with real-time updates.
        
        Yields:
            Chunks of the response as they're generated
        """
        agent_executor = self._create_agent_executor(db, user)
        
        # Convert chat history
        history_messages = []
        if chat_history:
            for msg in chat_history[-10:]:
                role = msg.get("role")
                content = msg.get("content")
                
                if role == "user":
                    history_messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    history_messages.append(AIMessage(content=content))
        
        try:
            # Use astream_events for real streaming
            config = RunnableConfig(recursion_limit=10)
            
            async for event in agent_executor.astream_events(
                {
                    "input": message,
                    "chat_history": history_messages,
                },
                config=config,
                version="v1"
            ):
                # Filter for LLM token events
                kind = event.get("event")
                
                if kind == "on_chat_model_stream":
                    content = event.get("data", {}).get("chunk", {})
                    if hasattr(content, "content"):
                        chunk_text = content.content
                        if chunk_text:
                            yield chunk_text
                
                # Also handle direct content chunks
                elif kind == "on_llm_new_token":
                    token = event.get("data", {}).get("chunk")
                    if token:
                        yield str(token)
        
        except Exception as e:
            print(f"❌ Streaming error: {e}")
            import traceback
            traceback.print_exc()
            yield f"\n\nI encountered an error: {str(e)}"



