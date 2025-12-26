from claude_agent_sdk import AgentDefinition, ClaudeAgentOptions

from app.agents.base import BaseAgent
from app.agents.deepresearch.config import (
    MODEL,
    NOTION_TOKEN,
    NOTION_PARENT_PAGE_ID,
    MAX_TURNS,
    MCP_SERVERS,
    SEARCH_DEPTH,
    MAX_RESULTS,
    RESEARCHER_MODEL,
)
from app.agents.deepresearch.prompts.lead_agent import get_lead_agent_prompt
from app.agents.deepresearch.prompts.researcher import get_researcher_prompt
from app.agents.deepresearch.schema import NOTION_OUTPUT_SCHEMA
from app.services.notion import (
    NotionService,
    blocks_to_notion_format,
    parse_agent_output,
)


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
                model=RESEARCHER_MODEL,
            ),
        }

        return ClaudeAgentOptions(
            model=MODEL,
            max_turns=MAX_TURNS,
            permission_mode="bypassPermissions",
            mcp_servers=MCP_SERVERS,
            agents=agents,
            allowed_tools=["Task"],
            output_format=NOTION_OUTPUT_SCHEMA,
        )

    def get_input_data(self, topic: str) -> dict:
        return {"topic": topic}

    async def process_structured_output(self, structured_output: dict, **kwargs) -> None:
        """处理结构化输出，写入 Notion"""
        if not structured_output:
            return

        self._write_to_notion(structured_output)

    async def process_final_output(self, final_text: str, **kwargs) -> None:
        """处理文本输出（回退方案），解析 JSON 后写入 Notion"""
        if not final_text:
            return

        parsed = parse_agent_output(final_text)
        self._write_to_notion(parsed)

    def _write_to_notion(self, data: dict) -> None:
        """写入 Notion 页面"""
        notion_blocks = blocks_to_notion_format(data["blocks"])

        notion_service = NotionService(NOTION_TOKEN)
        notion_service.create_page(
            parent_page_id=NOTION_PARENT_PAGE_ID,
            title=data["title"],
            blocks=notion_blocks,
        )


async def run_deepresearch_agent(topic: str) -> None:
    """执行 DeepResearch Agent"""
    agent = DeepResearchAgent()
    await agent.run(topic=topic)
