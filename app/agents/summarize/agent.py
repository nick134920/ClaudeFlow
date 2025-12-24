from claude_agent_sdk import ClaudeAgentOptions

from app.agents.base import BaseAgent
from app.agents.summarize.config import NOTION_PARENT_PAGE_ID, MAX_TURNS

# MCP 服务器配置
MCP_SERVERS = {
    "firecrawl": {
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "firecrawl-mcp"],
        "env": {
            "FIRECRAWL_API_KEY": "REDACTED_FIRECRAWL_KEY"
        }
    },
    "notion": {
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@notionhq/notion-mcp-server"],
        "env": {
            "NOTION_TOKEN": "REDACTED_NOTION_TOKEN"
        }
    }
}


class SummarizeAgent(BaseAgent):
    """URL 摘要 Agent - 抓取 URL 内容并创建 Notion 页面"""

    MODULE_NAME = "summarize"

    def get_prompt(self, url: str) -> str:
        return f"""
请完成以下任务：

1. 使用 mcp__firecrawl__firecrawl_scrape 工具抓取这个 URL 的内容：{url}

2. 为抓取的内容生成一个简洁的中文标题（10字以内）

3. 将内容总结为 Markdown 格式，包含：
   - 核心要点（3-5 条）
   - 详细总结（200-300字）

4. 使用 mcp__notion__API-post-page 工具在父页面 {NOTION_PARENT_PAGE_ID} 下创建一个新 Page：
   - 标题：生成的中文标题
   - 内容：Markdown 格式的总结
"""

    def get_options(self) -> ClaudeAgentOptions:
        return ClaudeAgentOptions(
            max_turns=MAX_TURNS,
            permission_mode="bypassPermissions",  # 自动批准所有工具使用
            mcp_servers=MCP_SERVERS,
        )

    def get_input_data(self, url: str) -> dict:
        return {"url": url}


async def run_summarize_agent(url: str) -> None:
    """执行 summarize Agent"""
    agent = SummarizeAgent()
    await agent.run(url=url)
