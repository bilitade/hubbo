# Hubbo Agentic AI System 🤖

## Overview

Hubbo Chat now features a **powerful agentic AI system** that can intelligently query your database and provide real-time, context-aware answers about your projects, tasks, and team.

## Architecture

```
User Question
    ↓
Agent Service (LangChain)
    ↓
Tool Selection (Automatic)
    ↓
Database Query
    ↓
Contextual Response
```

## Components

### 1. **Tools** (`app/ai/tools.py`)

Six specialized tools that fetch real data:

#### `get_projects`
- **Purpose**: Fetch project information
- **Parameters**: 
  - `status`: Filter by status (planning, not_started, in_progress, done)
  - `limit`: Max number of results
- **Example Questions**:
  - "What projects are currently in progress?"
  - "Show me all planning phase projects"

#### `get_tasks`
- **Purpose**: Fetch task information
- **Parameters**:
  - `status`: Filter by status (unassigned, in_progress, done)
  - `project_id`: Filter by specific project
  - `limit`: Max number of results
- **Example Questions**:
  - "What tasks are in progress?"
  - "Show me unassigned tasks"

#### `get_overdue_projects`
- **Purpose**: Find projects past their due date
- **Example Questions**:
  - "Which projects are overdue?"
  - "Show me delayed projects"
  - "What's behind schedule?"

#### `get_project_stats`
- **Purpose**: Get overall system statistics
- **Example Questions**:
  - "Give me an overview of all projects"
  - "What's the overall project status?"
  - "How many tasks do we have?"

#### `get_user_workload`
- **Purpose**: Analyze team workload distribution
- **Parameters**:
  - `limit`: Max number of users
- **Example Questions**:
  - "Who has the most tasks?"
  - "Show me team workload"
  - "What's the task distribution?"

#### `get_ideas`
- **Purpose**: Fetch ideas from the system
- **Parameters**:
  - `limit`: Max number of ideas
- **Example Questions**:
  - "What ideas do we have?"
  - "Show me recent brainstorming results"

### 2. **Agent Service** (`app/ai/agent_service.py`)

The brain of the system:

- **Uses LangChain's OpenAI Tools Agent**
- **Automatic tool selection** based on user question
- **Multi-step reasoning** (up to 5 iterations)
- **Error handling** with fallback
- **Conversation history** support

### 3. **Chat Service Integration** (`app/ai/chat_service_sync.py`)

Seamlessly integrated into Hubbo Chat:

- **Primary**: Uses agent for tool-based responses
- **Fallback**: Uses simple LLM if agent fails
- **Thread context**: Maintains conversation history
- **User context**: Passes user information to agent

## How It Works

### Example 1: Project Status Query

**User**: "What projects are currently in progress?"

**Agent Process**:
1. Analyzes question
2. Selects `get_projects` tool
3. Calls tool with `status="in_progress"`
4. Receives JSON data from database
5. Formats data into natural language
6. Returns: "You have 3 projects in progress: Project A, Project B, and Project C..."

### Example 2: Overdue Analysis

**User**: "Which projects are overdue?"

**Agent Process**:
1. Analyzes question about deadlines
2. Selects `get_overdue_projects` tool
3. Queries database for projects past due date
4. Returns: "You have 2 overdue projects: Project X (3 days late) and Project Y (7 days late)..."

### Example 3: Multi-Tool Query

**User**: "Give me a complete overview of our current status"

**Agent Process**:
1. Uses `get_project_stats` for overall metrics
2. Uses `get_overdue_projects` to check delays
3. Uses `get_user_workload` for team info
4. Combines all data
5. Returns comprehensive summary

## Benefits

### 🎯 **Accurate Information**
- No hallucinations - data comes directly from your database
- Real-time information, always up-to-date

### 🧠 **Intelligent Understanding**
- Understands natural language questions
- Selects appropriate tools automatically
- Can combine multiple data sources

### 📊 **Actionable Insights**
- Highlights issues (overdue projects)
- Analyzes workload distribution
- Provides context and recommendations

### 💬 **Conversational**
- Maintains chat history
- Understands follow-up questions
- Natural language responses

## Usage Examples

### Project Management

```
User: "What's the status of all my projects?"
Agent: Uses get_project_stats, returns overview

User: "Are any of them overdue?"
Agent: Uses get_overdue_projects, identifies delays

User: "Show me tasks for Project Alpha"
Agent: Uses get_tasks with project filter
```

### Team Management

```
User: "Who has the most tasks assigned?"
Agent: Uses get_user_workload, ranks by task count

User: "What's John's current workload?"
Agent: Uses get_user_workload, filters for John
```

### Quick Insights

```
User: "Give me a project summary"
Agent: Uses get_project_stats

User: "What should I focus on today?"
Agent: Uses get_overdue_projects + get_tasks
```

## Configuration

The system uses your existing LLM configuration:

```python
# Defined in app/config/settings.py
AI_PROVIDER = "openai"  # or "anthropic"
AI_MODEL = "gpt-4"      # or your preferred model
```

## Error Handling

The system has robust error handling:

1. **Agent Failure**: Falls back to simple LLM
2. **Tool Failure**: Returns helpful error message
3. **Empty Results**: Informs user gracefully
4. **Parsing Errors**: Handled automatically

## Extending the System

### Adding New Tools

1. **Create Tool Class** in `app/ai/tools.py`:

```python
class GetCustomDataTool(BaseTool):
    name: str = "get_custom_data"
    description: str = "Fetch custom data..."
    
    def _run(self, param: str) -> str:
        # Your logic here
        return json.dumps(result)
```

2. **Register Tool** in `create_tools()`:

```python
def create_tools(db: Session) -> List[BaseTool]:
    return [
        GetProjectsTool(db=db),
        # ... existing tools ...
        GetCustomDataTool(db=db),  # Add here
    ]
```

### Customizing Agent Behavior

Edit the system prompt in `agent_service.py`:

```python
def _create_agent_prompt(self) -> ChatPromptTemplate:
    system_message = """You are Hubbo AI...
    
    [Customize behavior here]
    """
```

## Performance

- **Tool Execution**: < 100ms (database queries)
- **LLM Response**: 1-3 seconds (depends on model)
- **Total Response Time**: 2-5 seconds average

## Security

- Tools only access data user has permission to see
- Database queries use user context
- Input sanitization applied
- No direct database modification through tools

## Future Enhancements

Possible additions:

- **File Search Tool**: Search uploaded documents
- **Calendar Tool**: Check deadlines and schedules
- **Analytics Tool**: Generate reports and charts
- **Action Tools**: Create/update tasks (with confirmation)
- **Export Tool**: Generate reports in PDF/Excel
- **Notification Tool**: Set reminders

## Testing

Test the agent with various questions:

```bash
# In Python shell
from app.ai.agent_service import AgentService
from app.db.session import SessionLocal

db = SessionLocal()
agent = AgentService()

# Test query
response = agent.quick_answer(
    db=db,
    question="What projects are overdue?",
    user=current_user
)
print(response)
```

## Troubleshooting

### Agent not using tools

**Issue**: Agent responds without querying database

**Solution**: Make question more specific:
- Bad: "Tell me about projects"
- Good: "What's the status of all my projects?"

### Slow responses

**Issue**: Agent takes too long

**Solution**: 
- Check database indexes
- Limit results with `limit` parameter
- Use simpler questions

### No data returned

**Issue**: Tools return "No data found"

**Solution**:
- Verify data exists in database
- Check user permissions
- Try broader query parameters

## Summary

The Hubbo Agentic AI System transforms Hubbo Chat from a simple chatbot into an **intelligent project management assistant** that:

✅ Understands natural language questions
✅ Queries your database automatically  
✅ Provides accurate, real-time answers
✅ Offers insights and recommendations
✅ Maintains conversation context
✅ Handles errors gracefully

Ask it anything about your projects - it's like having a smart analyst on your team! 🚀




