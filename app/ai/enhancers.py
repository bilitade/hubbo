"""AI enhancers for Ideas, Projects, and Tasks using LangChain."""
from typing import Optional, Dict, Any, List
from langchain_core.messages import HumanMessage, SystemMessage
from app.ai.llm_factory import LLMFactory
from app.ai.config import LLMConfig
import re
import json


class IdeaEnhancer:
    """Enhance ideas with AI-generated improvements."""
    
    def __init__(self, llm_config: Optional[LLMConfig] = None):
        """Initialize with LLM."""
        self.llm = LLMFactory.create_llm(llm_config)
    
    async def enhance_idea(
        self,
        title: str,
        description: Optional[str] = None,
        possible_outcome: Optional[str] = None,
        departments: Optional[List[str]] = None,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Enhance an idea with AI-generated improvements.
        
        Args:
            title: Current idea title
            description: Current description
            possible_outcome: Current possible outcome
            departments: Departments affected
            category: Idea category
            
        Returns:
            Enhanced idea fields
        """
        system_prompt = """You are an innovation consultant helping improve business ideas.

INSTRUCTIONS:
- Improve the title to be clear, compelling, and professional
- Expand the description with more details and context
- Enhance possible outcomes to be specific and measurable
- Keep the core concept but make it more actionable
- Be concise but comprehensive

Format your response as:
TITLE: [improved title]
DESCRIPTION: [improved description]
OUTCOME: [improved possible outcome]"""

        # Build context
        context_parts = [f"Current Title: {title}"]
        if description:
            context_parts.append(f"Current Description: {description}")
        if possible_outcome:
            context_parts.append(f"Current Outcome: {possible_outcome}")
        if departments:
            context_parts.append(f"Departments: {', '.join(departments)}")
        if category:
            context_parts.append(f"Category: {category}")
        
        user_message = "\n".join(context_parts) + "\n\nPlease improve this idea."
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]
        
        response = await self.llm.ainvoke(messages)
        ai_response = response.content
        
        # Parse response
        parsed = {}
        
        title_match = re.search(r'TITLE:\s*(.+?)(?:\n|$)', ai_response, re.IGNORECASE)
        if title_match:
            parsed['title'] = title_match.group(1).strip()
        
        desc_match = re.search(r'DESCRIPTION:\s*(.+?)(?:\n(?:OUTCOME|$))', ai_response, re.IGNORECASE | re.DOTALL)
        if desc_match:
            parsed['description'] = desc_match.group(1).strip()
        
        outcome_match = re.search(r'OUTCOME:\s*(.+?)(?:\n|$)', ai_response, re.IGNORECASE | re.DOTALL)
        if outcome_match:
            parsed['possible_outcome'] = outcome_match.group(1).strip()
        
        return {
            "success": True,
            "enhanced_data": parsed,
            "raw_response": ai_response
        }


class ProjectEnhancer:
    """Enhance projects with AI-generated details."""
    
    def __init__(self, llm_config: Optional[LLMConfig] = None):
        """Initialize with LLM."""
        self.llm = LLMFactory.create_llm(llm_config)
    
    async def enhance_project(
        self,
        title: str,
        description: Optional[str] = None,
        tag: Optional[str] = None,
        brief: Optional[str] = None,
        desired_outcomes: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Enhance a project with AI-generated details.
        
        Args:
            title: Project title
            description: Project description
            tag: Current tag
            brief: Current brief
            desired_outcomes: Current outcomes
            context: Additional context
            
        Returns:
            Enhanced project fields
        """
        system_prompt = """You are a project management expert helping enhance project details.

INSTRUCTIONS:
- Improve the title to be clear and professional
- Enhance the description with more context and goals
- Suggest a single UPPERCASE tag that captures the essence
- Create a detailed brief with 5-8 bullet points of key features/deliverables
- Define 3-5 specific, measurable desired outcomes
- Be professional and actionable

Format your response as:
TITLE: [improved title]
DESCRIPTION: [improved description]
TAG: [UPPERCASE_TAG]
BRIEF:
- Feature/deliverable 1
- Feature/deliverable 2
...
OUTCOMES:
- Outcome 1
- Outcome 2
..."""

        # Build context
        context_parts = [f"Project Title: {title}"]
        if description:
            context_parts.append(f"Description: {description}")
        if tag:
            context_parts.append(f"Current Tag: {tag}")
        if brief:
            context_parts.append(f"Current Brief: {brief}")
        if desired_outcomes:
            context_parts.append(f"Current Outcomes: {desired_outcomes}")
        if context:
            for key, value in context.items():
                context_parts.append(f"{key}: {value}")
        
        user_message = "\n".join(context_parts) + "\n\nPlease enhance this project with comprehensive details."
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]
        
        response = await self.llm.ainvoke(messages)
        ai_response = response.content
        
        # Parse response
        parsed = self._parse_project_response(ai_response)
        
        return {
            "success": True,
            "enhanced_data": parsed,
            "raw_response": ai_response
        }
    
    def _parse_project_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response into structured project data."""
        parsed = {}
        
        # Extract title
        title_match = re.search(r'TITLE:\s*(.+?)(?:\n|$)', response, re.IGNORECASE)
        if title_match:
            parsed['title'] = title_match.group(1).strip()
        
        # Extract description
        desc_match = re.search(r'DESCRIPTION:\s*(.+?)(?:\n(?:TAG|BRIEF|OUTCOMES|$))', response, re.IGNORECASE | re.DOTALL)
        if desc_match:
            parsed['description'] = desc_match.group(1).strip()
        
        # Extract tag
        tag_match = re.search(r'TAG:\s*(\w+)', response, re.IGNORECASE)
        if tag_match:
            parsed['tag'] = tag_match.group(1).upper()
        
        # Extract brief (as list)
        brief_match = re.search(r'BRIEF:\s*\n((?:[-•]\s*.+\n?)+)', response, re.IGNORECASE)
        if brief_match:
            brief_text = brief_match.group(1)
            brief_items = re.findall(r'[-•]\s*(.+)', brief_text)
            parsed['brief'] = brief_items
            # Also provide as formatted string
            parsed['brief_text'] = "\n".join(f"- {item.strip()}" for item in brief_items)
        
        # Extract outcomes (as list)
        outcomes_match = re.search(r'OUTCOMES:\s*\n((?:[-•]\s*.+\n?)+)', response, re.IGNORECASE)
        if outcomes_match:
            outcomes_text = outcomes_match.group(1)
            outcome_items = re.findall(r'[-•]\s*(.+)', outcomes_text)
            parsed['desired_outcomes'] = outcome_items
            # Also provide as formatted string
            parsed['desired_outcomes_text'] = "\n".join(f"- {item.strip()}" for item in outcome_items)
        
        return parsed


class TaskGenerator:
    """Generate tasks and subtasks for projects using AI."""
    
    def __init__(self, llm_config: Optional[LLMConfig] = None):
        """Initialize with LLM."""
        self.llm = LLMFactory.create_llm(llm_config)
    
    async def generate_tasks(
        self,
        project_title: str,
        project_description: Optional[str] = None,
        project_brief: Optional[str] = None,
        project_outcomes: Optional[str] = None,
        workflow_step: Optional[int] = None,
        num_tasks: int = 5
    ) -> Dict[str, Any]:
        """
        Generate tasks and subtasks for a project.
        
        Args:
            project_title: Project title
            project_description: Project description
            project_brief: Project brief/features
            project_outcomes: Desired outcomes
            workflow_step: Current workflow step
            num_tasks: Number of tasks to generate
            
        Returns:
            List of tasks with subtasks
        """
        system_prompt = f"""You are a project management expert creating detailed task breakdowns.

INSTRUCTIONS:
- Generate {num_tasks} main tasks for this project
- Each task should have a clear title and description
- Each task should have 3-5 subtasks (activities)
- Tasks should be logical, sequential, and comprehensive
- Include estimated priority (high, medium, low)
- Be specific and actionable

Format your response as JSON:
{{
  "tasks": [
    {{
      "title": "Task title",
      "description": "Task description",
      "priority": "high|medium|low",
      "activities": [
        "Subtask 1",
        "Subtask 2",
        "Subtask 3"
      ]
    }}
  ]
}}"""

        # Build context
        context_parts = [f"Project: {project_title}"]
        if project_description:
            context_parts.append(f"Description: {project_description}")
        if project_brief:
            context_parts.append(f"Features/Brief: {project_brief}")
        if project_outcomes:
            context_parts.append(f"Desired Outcomes: {project_outcomes}")
        if workflow_step:
            context_parts.append(f"Current Workflow Step: {workflow_step}")
        
        user_message = "\n".join(context_parts) + f"\n\nPlease generate {num_tasks} comprehensive tasks with subtasks."
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]
        
        response = await self.llm.ainvoke(messages)
        ai_response = response.content
        
        # Try to parse JSON response
        tasks = self._parse_tasks_response(ai_response)
        
        return {
            "success": True,
            "tasks": tasks,
            "raw_response": ai_response
        }
    
    def _parse_tasks_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse AI response into structured task data."""
        # Try to extract JSON
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            try:
                data = json.loads(json_match.group(0))
                if 'tasks' in data:
                    return data['tasks']
            except json.JSONDecodeError:
                pass
        
        # Fallback: Parse manually
        tasks = []
        task_pattern = r'(?:TASK|Task)\s*\d*[:\.]?\s*(.+?)(?:\n|$)'
        desc_pattern = r'(?:DESCRIPTION|Description)[:\.]?\s*(.+?)(?:\n|$)'
        activities_pattern = r'(?:ACTIVITIES|SUBTASKS|Activities|Subtasks)[:\.]?\s*\n((?:[-•]\s*.+\n?)+)'
        
        task_matches = re.finditer(task_pattern, response, re.IGNORECASE)
        for match in task_matches:
            task_title = match.group(1).strip()
            
            # Find description after this task
            desc_match = re.search(desc_pattern, response[match.end():match.end()+500], re.IGNORECASE)
            task_desc = desc_match.group(1).strip() if desc_match else ""
            
            # Find activities after this task
            activities = []
            act_match = re.search(activities_pattern, response[match.end():match.end()+1000], re.IGNORECASE)
            if act_match:
                act_text = act_match.group(1)
                activities = [a.strip() for a in re.findall(r'[-•]\s*(.+)', act_text)]
            
            if task_title:
                tasks.append({
                    "title": task_title,
                    "description": task_desc,
                    "priority": "medium",
                    "activities": activities
                })
        
        return tasks
