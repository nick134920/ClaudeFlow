# app/agents/newprojectanalyse/handlers/web.py
from claude_agent_sdk import AgentDefinition

from app.agents.newprojectanalyse.prompts.web import get_web_prompt


def get_web_agent_definition(url: str) -> AgentDefinition:
    """
    返回 Web 分析 subagent 的定义

    Args:
        url: 网页 URL
    """
    return AgentDefinition(
        description="分析网页内容，提取核心信息并总结",
        prompt=get_web_prompt(url),
        tools=["mcp__firecrawl__firecrawl_scrape"],
        model="sonnet",
    )
