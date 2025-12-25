from datetime import datetime

from claude_agent_sdk import ClaudeAgentOptions

from app.agents.base import BaseAgent
from app.agents.deepresearch.config import (
    MODEL,
    NOTION_PARENT_PAGE_ID,
    MAX_TURNS,
    MCP_SERVERS,
    SEARCH_DEPTH,
    MAX_RESULTS,
    RESEARCH_NOTES_DIR,
)
from app.agents.deepresearch.prompts.lead_agent import get_lead_agent_prompt
from app.agents.deepresearch.prompts.researcher import get_researcher_prompt
from app.agents.deepresearch.prompts.notion_writer import get_notion_writer_prompt


class DeepResearchAgent(BaseAgent):
    """深度研究 Agent - 多 Agent 协作完成研究任务"""

    MODULE_NAME = "deepresearch"

    def __init__(self):
        super().__init__()
        # 确保研究笔记目录存在
        RESEARCH_NOTES_DIR.mkdir(parents=True, exist_ok=True)

    def get_prompt(self, topic: str) -> str:
        return get_lead_agent_prompt(topic)

    def get_options(self) -> ClaudeAgentOptions:
        # 构建 subagent 定义
        agents = {
            "researcher": {
                "description": "使用 Tavily 搜索指定子课题，将结果写入 research_notes/",
                "prompt": get_researcher_prompt(
                    search_depth=SEARCH_DEPTH,
                    max_results=MAX_RESULTS,
                    research_notes_dir=str(RESEARCH_NOTES_DIR),
                ),
                "tools": ["mcp__tavily__tavily-search", "Write"],
                "model": "haiku",
            },
            "notion-writer": {
                "description": "读取研究笔记，综合后创建 Notion 子页面",
                "prompt": get_notion_writer_prompt(
                    notion_parent_page_id=NOTION_PARENT_PAGE_ID,
                    research_notes_dir=str(RESEARCH_NOTES_DIR),
                ),
                "tools": [
                    "Read",
                    "Glob",
                    "mcp__notion__API-post-page",
                    "mcp__notion__API-patch-block-children",
                ],
                "model": "sonnet",
            },
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
