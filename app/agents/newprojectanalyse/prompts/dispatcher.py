# app/agents/newprojectanalyse/prompts/dispatcher.py

def get_dispatcher_prompt(url: str, github_content: tuple[str, str, str] | None) -> str:
    """
    入口 agent 的分发 prompt

    Args:
        url: 目标 URL
        github_content: GitHub 仓库内容 (summary, tree, content)，如果是 GitHub URL 且预获取成功
    """
    context = ""
    if github_content:
        summary, _tree, content = github_content
        context = f"""
## 预获取的 GitHub 仓库内容

### 概要
{summary}

### 文件内容
{content}
"""

    return f"""
请分析以下 URL：{url}

{context}

## 任务

根据 URL 类型选择合适的分析方式：

1. 如果是 GitHub 仓库（已提供预获取内容），调用 github_analyser
2. 如果是普通网页，调用 web_analyser

调用对应的 subagent 完成分析，将其返回的结果直接作为最终输出。

## 输出格式

将 subagent 返回的 JSON 结果原样输出，格式：
```json
{{"title": "...", "blocks": [...]}}
```
"""
