# app/agents/newprojectanalyse/handlers/github.py
from claude_agent_sdk import AgentDefinition

from app.agents.newprojectanalyse.prompts.github import get_github_prompt


def get_github_agent_definition(url: str, summary: str, content: str) -> AgentDefinition:
    """
    返回 GitHub 分析 subagent 的定义

    Args:
        url: GitHub 仓库 URL
        summary: gitingest 获取的仓库概要
        content: gitingest 获取的文件内容
    """
    return AgentDefinition(
        description="分析 GitHub 仓库，提取项目信息、技术栈、部署说明等",
        prompt=get_github_prompt(url, summary, content),
        tools=["mcp__fetch__fetch"],
        model="sonnet",
    )
