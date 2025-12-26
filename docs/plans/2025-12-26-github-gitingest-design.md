# GitHub 仓库 gitingest 分析功能设计

## 概述

为 `NewProjectAnalyseAgent` 增加 GitHub 仓库识别和 gitingest 分析功能。当检测到输入 URL 为 GitHub 仓库时，使用 gitingest 包获取仓库完整内容进行深度分析，替代原有的 firecrawl 抓取方式。

## 架构设计

```
URL 输入
    │
    ▼
┌─────────────────────┐
│ 判断是否为 GitHub   │
│ 仓库 URL            │
└─────────────────────┘
    │
    ├── 是 GitHub ──► 调用 gitingest ──► 注入内容到 Prompt
    │                                    （不使用 firecrawl）
    │
    └── 非 GitHub ──► 保持现有流程
                      （使用 firecrawl 抓取）
```

## 实现细节

### 1. GitHub URL 判断

```python
import re

def is_github_repo_url(url: str) -> bool:
    """判断是否为 GitHub 仓库 URL"""
    pattern = r'^https?://github\.com/[\w.-]+/[\w.-]+/?'
    return bool(re.match(pattern, url))
```

### 2. gitingest 调用

```python
from gitingest import ingest_async

async def fetch_github_repo_content(url: str) -> tuple[str, str, str]:
    """获取 GitHub 仓库内容"""
    exclude_patterns = [
        "node_modules/*", "vendor/*", ".venv/*", "venv/*",
        "dist/*", "build/*", ".git/*",
        "*.lock", "*.min.js", "*.min.css",
        "*.log", "*.pyc", "__pycache__/*"
    ]

    summary, tree, content = await ingest_async(
        url,
        exclude_patterns=exclude_patterns
    )
    return summary, tree, content
```

### 3. Prompt 拆分

将 `get_prompt()` 拆分为两个方法：

- `get_prompt_for_github(url, summary, tree, content)` - GitHub 仓库专用
- `get_prompt_for_web(url)` - 非 GitHub URL（保持现有逻辑）

### 4. run() 方法修改

在调用 `get_prompt()` 之前预处理：

```python
async def run(self, **kwargs) -> None:
    url = kwargs.get("url")

    if is_github_repo_url(url):
        summary, tree, content = await fetch_github_repo_content(url)
        prompt = self.get_prompt_for_github(url, summary, tree, content)
    else:
        prompt = self.get_prompt_for_web(url)

    # 继续现有流程...
```

## JSON 输出格式

新增两个内容块，位于「核心逻辑思维导图」之后：

```json
{
  "title": "项目名称-中文标题-20241226",
  "blocks": [
    {"type": "bookmark", "url": "..."},
    {"type": "callout", "content": "⭐ Stars: ... | 🍴 Forks: ...", "emoji": "📊"},
    {"type": "divider"},
    {"type": "heading_1", "content": "项目概述"},
    {"type": "paragraph", "content": "..."},
    {"type": "heading_1", "content": "核心要点"},
    {"type": "bulleted_list", "items": ["...", "..."]},
    {"type": "heading_1", "content": "详细总结"},
    {"type": "paragraph", "content": "..."},
    {"type": "heading_1", "content": "核心逻辑思维导图"},
    {"type": "bulleted_list", "items": [...]},

    {"type": "heading_1", "content": "项目结构"},
    {"type": "code", "content": "目录树形结构...", "language": "text"},
    {"type": "paragraph", "content": "结构说明..."},

    {"type": "heading_1", "content": "部署说明"},
    {"type": "bulleted_list", "items": ["环境要求: ...", "安装步骤: ...", "启动命令: ..."]},

    {"type": "divider"},
    {"type": "paragraph", "content": "任务时间: ..."}
  ]
}
```

## 变更清单

### 新增依赖

- `gitingest`

### 文件变更

| 文件 | 变更内容 |
|------|----------|
| `app/agents/newprojectanalyse/agent.py` | 新增 GitHub 判断、gitingest 调用、Prompt 拆分 |
| `requirements.txt` / `pyproject.toml` | 添加 gitingest 依赖 |

### 不变的部分

- `app/services/notion.py` - Notion 服务层
- `app/agents/newprojectanalyse/config.py` - 配置结构
- 非 GitHub URL 的处理流程
