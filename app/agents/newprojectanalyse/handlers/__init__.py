# app/agents/newprojectanalyse/handlers/__init__.py
from app.agents.newprojectanalyse.handlers.github import get_github_agent_definition
from app.agents.newprojectanalyse.handlers.web import get_web_agent_definition

__all__ = ["get_github_agent_definition", "get_web_agent_definition"]
