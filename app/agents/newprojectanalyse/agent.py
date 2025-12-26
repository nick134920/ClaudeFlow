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
    "*.log", "*.pyc", "__pycache__/*",
    # lock 文件（非 .lock 后缀）
    "pnpm-lock.yaml", "package-lock.json", "bun.lockb",
]

# Prompt 调研所需的文件类型（用于快速分析项目结构和用途）
GITHUB_INCLUDE_PATTERNS = [
    # 文档文件（仅根目录和 docs 目录）
    "README*", "readme*", "CHANGELOG*", "LICENSE*", "CONTRIBUTING*",
    "*.md", "docs/*.md", "docs/**/*.md",
    # 配置文件
    "package.json", "pyproject.toml", "setup.py", "setup.cfg",
    "Cargo.toml", "go.mod", "pom.xml", "build.gradle",
    "Makefile", "Dockerfile", "docker-compose*.yml",
    "*.toml", "*.yaml", "*.yml", "*.json",
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
        include_patterns=GITHUB_INCLUDE_PATTERNS,
        exclude_patterns=GITHUB_EXCLUDE_PATTERNS,
    )
    return summary, tree, content


class NewProjectAnalyseAgent(BaseAgent):
    """新项目分析 Agent - 抓取项目 URL 内容并创建 Notion 页面"""

    MODULE_NAME = "newprojectanalyse"

    def get_prompt_for_web(self, url: str) -> str:
        """获取网站内容的 Prompt（使用 firecrawl 抓取）"""
        current_date = datetime.now().strftime("%Y%m%d")
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"""
请完成以下任务：

1. 使用 mcp__firecrawl__firecrawl_scrape 工具抓取这个 URL 的内容：{url}

2. 识别网站/文章的名称，并生成一个简洁的中文标题（10字以内）

3. 分析网页内容，提取核心信息并总结

4. 将内容总结并输出为以下 JSON 格式（必须用 ```json 包裹）：

```json
{{
  "title": "网站名称-中文标题-{current_date}",
  "blocks": [
    {{"type": "bookmark", "url": "{url}"}},
    {{"type": "divider"}},
    {{"type": "heading_1", "content": "内容概述"}},
    {{"type": "paragraph", "content": "网页内容的简要概述..."}},
    {{"type": "heading_1", "content": "核心要点"}},
    {{"type": "bulleted_list", "items": ["要点1", "要点2", "要点3", "要点4", "要点5"]}},
    {{"type": "heading_1", "content": "详细总结"}},
    {{"type": "paragraph", "content": "200-300字的详细总结，包含主要观点、关键信息等..."}},
    {{"type": "heading_1", "content": "内容结构"}},
    {{"type": "bulleted_list", "items": [
      {{"text": "主要章节1", "children": ["子内容1.1", "子内容1.2"]}},
      {{"text": "主要章节2", "children": ["子内容2.1", "子内容2.2"]}}
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
- title 格式必须为: "网站名称-中文标题-{current_date}"
- 任务时间必须放在内容最后
- 最终必须输出上述 JSON 格式
- JSON 必须用 ```json 代码块包裹
- 确保 JSON 格式正确，可以被解析
"""

    def get_prompt_for_github(self, url: str, summary: str, content: str) -> str:
        """获取 GitHub 仓库的 Prompt（使用 gitingest 内容）"""
        current_date = datetime.now().strftime("%Y%m%d")
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return f"""
请分析以下 GitHub 仓库：{url}

## 仓库信息（由 gitingest 获取）

### 概要
{summary}

### 文件内容
{content}

## 任务

1. 从 URL 中提取 owner 和 repo，使用 GitHub API 获取项目统计信息：
   - 访问 https://api.github.com/repos/{{owner}}/{{repo}} 获取 star、fork 数量和最后更新时间
   - 访问 https://api.github.com/repos/{{owner}}/{{repo}}/commits?per_page=1 获取最后 commit 时间

2. 基于以上内容，生成项目总结

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
    {{"type": "heading_1", "content": "部署说明"}},
    {{"type": "bulleted_list", "items": ["环境要求: ...", "安装步骤: ...", "启动命令: ..."]}},
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
- 禁止使用 firecrawl 工具，仓库内容已在上方提供
- 使用 mcp__fetch__fetch 工具访问 GitHub API 获取统计信息
- title 格式必须为: "项目名称-中文标题-{current_date}"
- 必须获取并显示 star/fork/最后提交时间，使用 callout 块展示
- 部署说明从 README、Dockerfile、package.json 等文件中提取
- 任务时间必须放在内容最后
- 最终必须输出上述 JSON 格式
- JSON 必须用 ```json 代码块包裹
- 确保 JSON 格式正确，可以被解析
"""

    def get_prompt(self, url: str, github_content: tuple[str, str, str] | None = None) -> str:
        """
        获取 Agent 提示词

        Args:
            url: 目标 URL
            github_content: GitHub 仓库内容 (summary, tree, content)，仅当 URL 为 GitHub 仓库时传入

        Returns:
            str: 生成的 Prompt
        """
        if github_content is not None:
            summary, _tree, content = github_content
            return self.get_prompt_for_github(url, summary, content)
        else:
            return self.get_prompt_for_web(url)

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

    async def pre_run(self, logger, **kwargs) -> dict:
        """
        运行前预处理：判断是否为 GitHub 仓库并获取内容

        Args:
            logger: TaskLogger 实例
            **kwargs: 包含 url 参数

        Returns:
            dict: 包含 github_content 的额外参数
        """
        url = kwargs.get("url")
        if not url:
            raise ValueError("url 参数是必需的")

        github_content = None
        if is_github_repo_url(url):
            logger.info("检测到 GitHub 仓库 URL，使用 gitingest 获取内容...")
            try:
                github_content = await fetch_github_repo_content(url)
                logger.info("gitingest 获取成功")
            except Exception as e:
                logger.warning(f"gitingest 获取失败，回退到 firecrawl: {e}")
                github_content = None

        return {"github_content": github_content}


async def run_newprojectanalyse_agent(url: str) -> None:
    """执行 newprojectanalyse Agent"""
    agent = NewProjectAnalyseAgent()
    await agent.run(url=url)
