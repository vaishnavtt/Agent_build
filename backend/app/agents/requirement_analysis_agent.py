"""Requirement Analysis Agent - Member 2 AI Agent Architect.

Wraps the LangGraph StateGraph requirement analysis workflow into an agent
class matching the AgentForge multi-agent architecture.
"""

from typing import Dict, Any, Optional
from app.services.requirement_analysis_service import RequirementAnalysisService
from app.schemas.requirement_analysis import ExecutionPlanResponse


class RequirementAnalysisAgent:
    """Specialized AI Agent for Requirement Analysis & Agent Architecture."""

    def __init__(self):
        self.service = RequirementAnalysisService()

    def analyze(
        self,
        description: str,
        clarification_answers: Optional[Dict[str, str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionPlanResponse:
        """Analyzes natural-language requirements and produces structured execution plan."""
        return self.service.analyze_requirements(
            description=description,
            clarification_answers=clarification_answers,
            context=context,
        )


# Global instance
requirement_agent = RequirementAnalysisAgent()
