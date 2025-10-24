"""AI-powered project information generator using LangChain."""
from typing import Optional, Dict, Any, Literal
from langchain_core.messages import HumanMessage, SystemMessage
from app.ai.llm_factory import LLMFactory
from app.ai.config import LLMConfig
from datetime import datetime
import re


OperationType = Literal[
    "project_title_description_generation",
    "project_details_generation",
    "project_full_generation"
]


class ProjectInfoGenerator:
    """Generate comprehensive project information using AI."""
    
    def __init__(self, llm_config: Optional[LLMConfig] = None):
        """Initialize with LLM."""
        self.llm = LLMFactory.create_llm(llm_config)
    
    async def generate_project_info(
        self,
        message: str,
        operation_type: OperationType = "project_details_generation",
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate project information based on operation type.
        
        Args:
            message: User's input/request
            operation_type: Type of generation to perform
            context: Additional context for generation
            user_id: User ID for logging
            user_email: User email for logging
            
        Returns:
            Dictionary with generated content
        """
        # Build system prompt based on operation type
        system_prompt = self._get_system_prompt(operation_type)
        
        # Prepare messages
        messages = [SystemMessage(content=system_prompt)]
        
        if context:
            context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
            messages.append(SystemMessage(content=f"Additional Context:\n{context_str}"))
        
        messages.append(HumanMessage(content=message))
        
        try:
            # Call LLM
            response = await self.llm.ainvoke(messages)
            ai_response = response.content
            
            # Parse response based on operation type
            parsed_data = self._parse_response(ai_response, operation_type)
            
            # TODO: Add logging here when AILogStorage is implemented
            
            return {
                "success": True,
                "response": ai_response,
                "parsed_data": parsed_data,
                "operation_type": operation_type
            }
            
        except Exception as e:
            # TODO: Add error logging here when AILogStorage is implemented
            raise
    
    def _get_system_prompt(self, operation_type: OperationType) -> str:
        """Get system prompt based on operation type."""
        
        if operation_type == "project_title_description_generation":
            return """You are a project planning assistant. Generate a professional project title and description.

INSTRUCTIONS:
- Title: Concise, clear, max 10 words
- Description: 2-3 sentences explaining goals and scope
- Be professional and actionable
- Focus on business value

Format:
TITLE: [title]
DESCRIPTION: [description]"""
        
        elif operation_type == "project_details_generation":
            return """You are a project planning assistant. Generate comprehensive project details.

INSTRUCTIONS:
- Tag: Single UPPERCASE word capturing essence
- Brief: 5-8 bullet points of expected features
- Outcomes: 3-5 bullet points of desired outcomes
- Be specific and actionable

Format:
TAG: [WORD]
BRIEF:
- Feature 1
- Feature 2
...
OUTCOMES:
- Outcome 1
- Outcome 2
..."""
        
        elif operation_type == "project_full_generation":
            return """You are a project planning assistant. Generate complete project information.

INSTRUCTIONS:
- Title: Concise, clear, max 10 words
- Description: 2-3 sentences explaining goals and scope
- Tag: Single UPPERCASE word capturing essence
- Brief: 5-8 bullet points of expected features
- Outcomes: 3-5 bullet points of desired outcomes
- Be professional, specific, and actionable

Format:
TITLE: [title]
DESCRIPTION: [description]
TAG: [WORD]
BRIEF:
- Feature 1
- Feature 2
...
OUTCOMES:
- Outcome 1
- Outcome 2
..."""
        
        else:
            return "You are a helpful project management assistant."
    
    def _parse_response(self, response: str, operation_type: OperationType) -> Dict[str, Any]:
        """Parse AI response into structured data."""
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
        
        # Extract brief (features)
        brief_match = re.search(r'BRIEF:\s*\n((?:[-•]\s*.+\n?)+)', response, re.IGNORECASE)
        if brief_match:
            brief_text = brief_match.group(1)
            brief_items = re.findall(r'[-•]\s*(.+)', brief_text)
            parsed['brief'] = [item.strip() for item in brief_items]
        
        # Extract outcomes
        outcomes_match = re.search(r'OUTCOMES:\s*\n((?:[-•]\s*.+\n?)+)', response, re.IGNORECASE)
        if outcomes_match:
            outcomes_text = outcomes_match.group(1)
            outcome_items = re.findall(r'[-•]\s*(.+)', outcomes_text)
            parsed['outcomes'] = [item.strip() for item in outcome_items]
        
        return parsed
    
    async def generate_title_description(
        self,
        idea_or_concept: str,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate project title and description.
        
        Args:
            idea_or_concept: The idea or concept to generate from
            context: Additional context
            user_id: User ID for logging
            user_email: User email for logging
            
        Returns:
            Dictionary with 'title' and 'description'
        """
        result = await self.generate_project_info(
            message=idea_or_concept,
            operation_type="project_title_description_generation",
            context=context,
            user_id=user_id,
            user_email=user_email
        )
        
        return result['parsed_data']
    
    async def generate_project_details(
        self,
        project_title: str,
        project_description: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate project details (tag, brief, outcomes).
        
        Args:
            project_title: Project title
            project_description: Optional project description
            context: Additional context
            user_id: User ID for logging
            user_email: User email for logging
            
        Returns:
            Dictionary with 'tag', 'brief', and 'outcomes'
        """
        message = f"Project: {project_title}"
        if project_description:
            message += f"\nDescription: {project_description}"
        
        result = await self.generate_project_info(
            message=message,
            operation_type="project_details_generation",
            context=context,
            user_id=user_id,
            user_email=user_email
        )
        
        return result['parsed_data']
    
    async def generate_full_project(
        self,
        idea_or_concept: str,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate complete project information.
        
        Args:
            idea_or_concept: The idea or concept to generate from
            context: Additional context
            user_id: User ID for logging
            user_email: User email for logging
            
        Returns:
            Dictionary with all project fields
        """
        result = await self.generate_project_info(
            message=idea_or_concept,
            operation_type="project_full_generation",
            context=context,
            user_id=user_id,
            user_email=user_email
        )
        
        return result['parsed_data']
