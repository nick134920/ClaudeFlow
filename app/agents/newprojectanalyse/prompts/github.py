# app/agents/newprojectanalyse/prompts/github.py
from datetime import datetime


def get_github_prompt(url: str, summary: str, content: str) -> str:
    """获取 GitHub 仓库分析的 Prompt"""
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
- 使用 mcp__fetch__fetch 工具访问 GitHub API 获取统计信息
- title 格式必须为: "项目名称-中文标题-{current_date}"
- 必须获取并显示 star/fork/最后提交时间，使用 callout 块展示
- 部署说明从 README、Dockerfile、package.json 等文件中提取
- 任务时间必须放在内容最后
- 最终必须输出上述 JSON 格式
- JSON 必须用 ```json 代码块包裹
- 确保 JSON 格式正确，可以被解析
"""
