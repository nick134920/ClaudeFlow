import re
from datetime import datetime

from claude_agent_sdk import ClaudeAgentOptions

from app.agents.base import BaseAgent
from app.agents.newprojectanalyse.config import (
    MODEL,
    NOTION_TOKEN,
    NOTION_PARENT_PAGE_ID,
    MAX_TURNS,
    MCP_SERVERS,
)
from app.services.notion import (
    NotionService,
    parse_agent_output,
    blocks_to_notion_format,
)


# GitHub 仓库 URL 排除模式
GITHUB_EXCLUDE_PATTERNS = [
    "node_modules/*", "vendor/*", ".venv/*", "venv/*",
    "dist/*", "build/*", ".git/*",
    "*.lock", "*.min.js", "*.min.css",
    "*.log", "*.pyc", "__pycache__/*"
]


def is_github_repo_url(url: str) -> bool:
    """判断是否为 GitHub 仓库 URL"""
    pattern = r'^https?://github\.com/[\w.-]+/[\w.-]+/?'
    return bool(re.match(pattern, url))


async def fetch_github_repo_content(url: str) -> tuple[str, str, str]:
    """
    获取 GitHub 仓库内容

    Args:
        url: GitHub 仓库 URL

    Returns:
        tuple: (summary, tree, content)
    """
    from gitingest import ingest_async

    summary, tree, content = await ingest_async(
        url,
        exclude_patterns=GITHUB_EXCLUDE_PATTERNS
    )
    return summary, tree, content


class NewProjectAnalyseAgent(BaseAgent):
    """新项目分析 Agent - 抓取项目 URL 内容并创建 Notion 页面"""

    MODULE_NAME = "newprojectanalyse"

    def get_prompt_for_web(self, url: str) -> str:
        """获取非 GitHub URL 的 Prompt（使用 firecrawl 抓取）"""
        current_date = datetime.now().strftime("%Y%m%d")
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"""
请完成以下任务：

1. 使用 mcp__firecrawl__firecrawl_scrape 工具抓取这个 URL 的内容：{url}

2. 如果是 GitHub 项目，使用 GitHub API 获取项目统计信息：
   - 访问 https://api.github.com/repos/{{owner}}/{{repo}} 获取 star、fork 数量和最后更新时间
   - 访问 https://api.github.com/repos/{{owner}}/{{repo}}/commits?per_page=1 获取最后 commit 时间

3. 识别项目名称，并生成一个简洁的中文标题（10字以内）

4. 将内容总结并输出为以下 JSON 格式（必须用 ```json 包裹）：

```json
{{
  "title": "项目名称-中文标题-{current_date}",
  "blocks": [
    {{"type": "bookmark", "url": "{url}"}},
    {{"type": "callout", "content": "⭐ Stars: 1234 | 🍴 Forks: 567 | 📅 最后提交: 2024-01-01", "emoji": "📊"}},
    {{"type": "divider"}},
    {{"type": "heading_1", "content": "项目概述"}},
    {{"type": "paragraph", "content": "项目简介..."}},
    {{"type": "heading_1", "content": "核心要点"}},
    {{"type": "bulleted_list", "items": ["要点1", "要点2", "要点3", "要点4", "要点5"]}},
    {{"type": "heading_1", "content": "详细总结"}},
    {{"type": "paragraph", "content": "200-300字的详细总结..."}},
    {{"type": "heading_1", "content": "核心逻辑思维导图"}},
    {{"type": "bulleted_list", "items": [
      {{"text": "主要模块1", "children": ["子模块1.1", "子模块1.2"]}},
      {{"text": "主要模块2", "children": ["子模块2.1", "子模块2.2"]}}
    ]}},
    {{"type": "divider"}},
    {{"type": "paragraph", "content": "任务时间: {current_time}"}}
  ]
}}
```

**支持的块类型:**
- heading_1, heading_2, heading_3: 标题（content 字段）
- paragraph: 段落（content 字段）
- bulleted_list: 无序列表，支持两种格式:
  - 简单列表: items 为字符串数组 ["item1", "item2"]
  - 嵌套列表: items 为对象数组 [{{"text": "父项", "children": ["子项1", "子项2"]}}]
- numbered_list: 有序列表（items 字段，字符串数组）
- code: 代码块（content 和 language 字段）
- divider: 分割线（无额外字段）
- bookmark: 书签链接（url 字段）
- callout: 标注块（content 和 emoji 字段）
- to_do: 待办事项（content 和 checked 字段）

**重要:**
- title 格式必须为: "项目名称-中文标题-{current_date}"
- 如果是 GitHub 项目，必须获取并显示 star/fork/最后提交时间，使用 callout 块单独展示
- 如果不是 GitHub 项目，省略 callout 块
- 任务时间必须放在内容最后
- 最终必须输出上述 JSON 格式
- JSON 必须用 ```json 代码块包裹
- 确保 JSON 格式正确，可以被解析
"""

    def get_options(self) -> ClaudeAgentOptions:
        return ClaudeAgentOptions(
            model=MODEL,
            max_turns=MAX_TURNS,
            permission_mode="bypassPermissions",
            mcp_servers=MCP_SERVERS,
        )

    def get_input_data(self, url: str) -> dict:
        return {"url": url}

    async def process_final_output(self, final_text: str, **kwargs) -> None:
        """处理最终输出，写入 Notion"""
        if not final_text:
            return

        parsed = parse_agent_output(final_text)
        notion_blocks = blocks_to_notion_format(parsed["blocks"])

        notion_service = NotionService(NOTION_TOKEN)
        notion_service.create_page(
            parent_page_id=NOTION_PARENT_PAGE_ID,
            title=parsed["title"],
            blocks=notion_blocks,
        )


async def run_newprojectanalyse_agent(url: str) -> None:
    """执行 newprojectanalyse Agent"""
    agent = NewProjectAnalyseAgent()
    await agent.run(url=url)
