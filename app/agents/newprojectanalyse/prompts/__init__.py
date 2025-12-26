# app/agents/newprojectanalyse/prompts/__init__.py
from app.agents.newprojectanalyse.prompts.dispatcher import get_dispatcher_prompt
from app.agents.newprojectanalyse.prompts.github import get_github_prompt
from app.agents.newprojectanalyse.prompts.web import get_web_prompt

__all__ = ["get_dispatcher_prompt", "get_github_prompt", "get_web_prompt"]
