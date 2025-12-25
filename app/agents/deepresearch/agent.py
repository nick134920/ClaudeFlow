from claude_agent_sdk import AgentDefinition, ClaudeAgentOptions

from app.agents.base import BaseAgent
from app.agents.deepresearch.config import (
    MODEL,
    NOTION_PARENT_PAGE_ID,
    MAX_TURNS,
    MCP_SERVERS,
    SEARCH_DEPTH,
    MAX_RESULTS,
)
from app.agents.deepresearch.prompts.lead_agent import get_lead_agent_prompt
from app.agents.deepresearch.prompts.researcher import get_researcher_prompt
from app.agents.deepresearch.prompts.notion_writer import get_notion_writer_prompt


class DeepResearchAgent(BaseAgent):
    """深度研究 Agent - 多 Agent 协作完成研究任务"""

    MODULE_NAME = "deepresearch"

    def get_prompt(self, topic: str) -> str:
        return get_lead_agent_prompt(topic)

    def get_options(self) -> ClaudeAgentOptions:
        # 构建 subagent 定义（使用 AgentDefinition 数据类）
        agents = {
            "researcher": AgentDefinition(
                description="使用 Tavily 搜索指定子课题，返回研究结果",
                prompt=get_researcher_prompt(
                    search_depth=SEARCH_DEPTH,
                    max_results=MAX_RESULTS,
                ),
                tools=["mcp__tavily__tavily-search"],
                model="haiku",
            ),
            "notion-writer": AgentDefinition(
                description="综合研究结果，创建 Notion 子页面",
                prompt=get_notion_writer_prompt(
                    notion_parent_page_id=NOTION_PARENT_PAGE_ID,
                ),
                tools=[
                    "mcp__notion__API-post-page",
                    "mcp__notion__API-patch-block-children",
                ],
                model="sonnet",
            ),
        }

        return ClaudeAgentOptions(
            model=MODEL,
            max_turns=MAX_TURNS,
            permission_mode="bypassPermissions",
            mcp_servers=MCP_SERVERS,
            agents=agents,
            allowed_tools=["Task"],
        )

    def get_input_data(self, topic: str) -> dict:
        return {"topic": topic}


async def run_deepresearch_agent(topic: str) -> None:
    """执行 DeepResearch Agent"""
    agent = DeepResearchAgent()
    await agent.run(topic=topic)
