# Hubbo Agentic AI - Quick Setup Guide

## 🚀 Getting Started

Your Hubbo Chat now has **agentic AI capabilities**! Here's how to set it up and use it.

## Prerequisites

Ensure you have an API key for one of these providers:

- **OpenAI** (recommended): GPT-4, GPT-3.5-turbo
- **Anthropic**: Claude models

## Setup Steps

### 1. Install Dependencies

The required packages should already be installed. If not:

```bash
cd /home/bilisuma/Desktop/hubbo/backend
pip install langchain langchain-openai langchain-anthropic
```

### 2. Configure API Keys

Your `.env` file should already have:

```env
# AI Configuration
OPENAI_API_KEY=your-key-here
# OR
ANTHROPIC_API_KEY=your-key-here

AI_PROVIDER=openai  # or anthropic
AI_MODEL=gpt-4      # or gpt-3.5-turbo, claude-3-sonnet, etc.
```

### 3. Run Database Migration

Create the chat tables:

```bash
cd /home/bilisuma/Desktop/hubbo/backend
python -m app.scripts.create_chat_tables
```

Expected output:
```
✅ Chat tables created successfully!
```

### 4. Start the Backend

```bash
uvicorn app.main:app --reload
```

### 5. Start the Frontend

```bash
cd /home/bilisuma/Desktop/hubbo/frontend
npm run dev
```

### 6. Access Hubbo Chat

1. Navigate to your app
2. Click on "Hubbo Chat" in the sidebar
3. Start asking questions!

## Testing the Agent

### Basic Test

Try these questions to verify the agent is working:

1. **"What's the status of all my projects?"**
   - Should use `get_project_stats` tool
   - Returns real project data

2. **"Which projects are overdue?"**
   - Should use `get_overdue_projects` tool
   - Returns projects past their due date

3. **"Who has the most tasks assigned?"**
   - Should use `get_user_workload` tool
   - Returns team workload distribution

### Verify Tool Usage

Check the backend console. You should see:

```
> Entering new AgentExecutor chain...
> Invoking: `get_projects` with `{'limit': 10}'
> ...
> Finished chain.
```

This confirms the agent is using tools!

## Example Conversations

### Scenario 1: Project Overview

```
You: "Give me an overview of our projects"

Hubbo: "You currently have 5 active projects:
- 2 in planning phase
- 1 not started
- 2 in progress

You have a total of 23 tasks, with 8 completed and 15 in progress."
```

### Scenario 2: Identify Issues

```
You: "Are there any overdue projects?"

Hubbo: "Yes, you have 1 overdue project:
- Project Alpha: 3 days overdue (due date was Jan 15)
  Owner: John Smith
  Status: in_progress"
```

### Scenario 3: Team Management

```
You: "What's our team's current workload?"

Hubbo: "Here's the team workload breakdown:
1. Sarah Johnson - 8 tasks (5 in progress, 3 done)
2. Mike Chen - 6 tasks (4 in progress, 2 done)
3. Emma Davis - 5 tasks (3 in progress, 2 done)

Sarah has the highest workload currently."
```

## Troubleshooting

### Issue: "AI service not configured"

**Solution**: Check your `.env` file has `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`

### Issue: "No projects found"

**Solution**: Make sure you have created some projects in the system

### Issue: Agent responds but doesn't use tools

**Symptoms**: Response is generic, no specific data

**Solutions**:
1. Check API key is valid
2. Use OpenAI GPT-4 or GPT-3.5-turbo (best tool support)
3. Make questions more specific
4. Check backend console for errors

### Issue: "Failed to resolve import"

**Solution**: Make sure all dependencies are installed:

```bash
pip install -r requirements.txt
```

## Configuration Options

### Change AI Model

Edit `.env`:

```env
# For OpenAI
AI_MODEL=gpt-4            # Most capable
AI_MODEL=gpt-3.5-turbo    # Faster, cheaper

# For Anthropic
AI_MODEL=claude-3-opus    # Most capable
AI_MODEL=claude-3-sonnet  # Balanced
```

### Adjust Agent Behavior

Edit `backend/app/ai/agent_service.py`:

```python
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,          # Set to False for less console output
    max_iterations=5,      # Max tool calls per question
    handle_parsing_errors=True,
)
```

## What Questions Can I Ask?

### Project Questions
- "What projects are currently active?"
- "Show me projects in planning phase"
- "Which projects are behind schedule?"
- "Give me a project status summary"

### Task Questions
- "What tasks are in progress?"
- "Show me unassigned tasks"
- "How many tasks are completed?"
- "What's the task breakdown?"

### Team Questions
- "Who has the most work?"
- "Show me team workload distribution"
- "What's everyone working on?"

### Combined Questions
- "Give me a complete status report"
- "What should I prioritize today?"
- "What are the biggest issues right now?"

## Next Steps

1. ✅ Test with sample questions
2. ✅ Verify tools are being used (check console)
3. ✅ Try complex multi-part questions
4. 📚 Read the full documentation: `AGENTIC_AI_SYSTEM.md`
5. 🛠️ Customize tools for your specific needs

## Need Help?

The agent will:
- ✅ Automatically select the right tools
- ✅ Query your database for real data
- ✅ Format responses in natural language
- ✅ Handle errors gracefully
- ✅ Fall back to simple chat if needed

Just ask questions naturally - the agent figures out the rest!

## Performance Tips

1. **Be Specific**: "What projects are overdue?" vs "Tell me about projects"
2. **One Topic**: Ask about one thing at a time for faster responses
3. **Use Limits**: Agent automatically limits results for speed
4. **Database**: Ensure proper indexes on your tables

## Success Indicators

You'll know it's working when:

✅ Backend shows "Entering new AgentExecutor chain..."
✅ You see tool invocations in the logs
✅ Responses include specific project/task names
✅ Data matches what's in your database
✅ Answers are detailed and accurate

---

**You're all set! Start chatting with Hubbo AI and watch it intelligently query your database!** 🎉




