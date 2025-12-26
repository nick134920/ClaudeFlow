# app/agents/newprojectanalyse/schema.py
"""NewProjectAnalyse Agent 输出 JSON Schema 定义"""

# GitHub 项目分析专用 Schema
# 使用具体字段而非自由 blocks 数组，确保输出内容符合预期
GITHUB_OUTPUT_SCHEMA = {
    "type": "json_schema",
    "schema": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "页面标题，格式: 项目名称-中文标题-日期"
            },
            "url": {
                "type": "string",
                "description": "GitHub 仓库 URL"
            },
            "stats": {
                "type": "object",
                "description": "GitHub 统计信息",
                "properties": {
                    "stars": {"type": "integer", "description": "Star 数量"},
                    "forks": {"type": "integer", "description": "Fork 数量"},
                    "last_commit": {"type": "string", "description": "最后提交时间"}
                },
                "required": ["stars", "forks", "last_commit"]
            },
            "overview": {
                "type": "string",
                "description": "项目概述（100-200字）"
            },
            "key_points": {
                "type": "array",
                "description": "核心要点（5个）",
                "items": {"type": "string"},
                "minItems": 3,
                "maxItems": 7
            },
            "detailed_summary": {
                "type": "string",
                "description": "详细总结（200-300字）"
            },
            "architecture": {
                "type": "array",
                "description": "核心逻辑/架构思维导图",
                "items": {
                    "type": "object",
                    "properties": {
                        "module": {"type": "string", "description": "主模块名"},
                        "children": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "子模块列表"
                        }
                    },
                    "required": ["module", "children"]
                }
            },
            "deployment": {
                "type": "object",
                "description": "部署说明",
                "properties": {
                    "requirements": {"type": "string", "description": "环境要求"},
                    "install_steps": {"type": "string", "description": "安装步骤"},
                    "start_command": {"type": "string", "description": "启动命令"}
                },
                "required": ["requirements", "install_steps", "start_command"]
            },
            "task_time": {
                "type": "string",
                "description": "任务完成时间"
            }
        },
        "required": [
            "title", "url", "stats", "overview", "key_points",
            "detailed_summary", "architecture", "deployment", "task_time"
        ],
        "additionalProperties": False
    }
}

# Web 页面分析专用 Schema
WEB_OUTPUT_SCHEMA = {
    "type": "json_schema",
    "schema": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "页面标题，格式: 网站名称-中文标题-日期"
            },
            "url": {
                "type": "string",
                "description": "网页 URL"
            },
            "overview": {
                "type": "string",
                "description": "内容概述（100-200字）"
            },
            "key_points": {
                "type": "array",
                "description": "核心要点（5个）",
                "items": {"type": "string"},
                "minItems": 3,
                "maxItems": 7
            },
            "detailed_summary": {
                "type": "string",
                "description": "详细总结（200-300字）"
            },
            "content_structure": {
                "type": "array",
                "description": "内容结构",
                "items": {
                    "type": "object",
                    "properties": {
                        "section": {"type": "string", "description": "章节名"},
                        "children": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "子内容列表"
                        }
                    },
                    "required": ["section", "children"]
                }
            },
            "task_time": {
                "type": "string",
                "description": "任务完成时间"
            }
        },
        "required": [
            "title", "url", "overview", "key_points",
            "detailed_summary", "content_structure", "task_time"
        ],
        "additionalProperties": False
    }
}


def github_output_to_blocks(data: dict) -> dict:
    """将 GitHub schema 输出转换为 Notion blocks 格式"""
    stats = data.get("stats", {})
    stats_text = f"⭐ Stars: {stats.get('stars', 'N/A')} | 🍴 Forks: {stats.get('forks', 'N/A')} | 📅 最后提交: {stats.get('last_commit', 'N/A')}"

    blocks = [
        {"type": "bookmark", "url": data["url"]},
        {"type": "callout", "content": stats_text, "emoji": "📊"},
        {"type": "divider"},
        {"type": "heading_1", "content": "项目概述"},
        {"type": "paragraph", "content": data["overview"]},
        {"type": "heading_1", "content": "核心要点"},
        {"type": "bulleted_list", "items": data["key_points"]},
        {"type": "heading_1", "content": "详细总结"},
        {"type": "paragraph", "content": data["detailed_summary"]},
        {"type": "heading_1", "content": "核心逻辑思维导图"},
        {"type": "bulleted_list", "items": [
            {"text": item["module"], "children": item["children"]}
            for item in data.get("architecture", [])
        ]},
        {"type": "heading_1", "content": "部署说明"},
        {"type": "bulleted_list", "items": [
            f"环境要求: {data['deployment']['requirements']}",
            f"安装步骤: {data['deployment']['install_steps']}",
            f"启动命令: {data['deployment']['start_command']}"
        ]},
        {"type": "divider"},
        {"type": "paragraph", "content": f"任务时间: {data['task_time']}"}
    ]

    return {"title": data["title"], "blocks": blocks}


def web_output_to_blocks(data: dict) -> dict:
    """将 Web schema 输出转换为 Notion blocks 格式"""
    blocks = [
        {"type": "bookmark", "url": data["url"]},
        {"type": "divider"},
        {"type": "heading_1", "content": "内容概述"},
        {"type": "paragraph", "content": data["overview"]},
        {"type": "heading_1", "content": "核心要点"},
        {"type": "bulleted_list", "items": data["key_points"]},
        {"type": "heading_1", "content": "详细总结"},
        {"type": "paragraph", "content": data["detailed_summary"]},
        {"type": "heading_1", "content": "内容结构"},
        {"type": "bulleted_list", "items": [
            {"text": item["section"], "children": item["children"]}
            for item in data.get("content_structure", [])
        ]},
        {"type": "divider"},
        {"type": "paragraph", "content": f"任务时间: {data['task_time']}"}
    ]

    return {"title": data["title"], "blocks": blocks}


# 保留旧的通用 schema 用于向后兼容
NOTION_OUTPUT_SCHEMA = {
    "type": "json_schema",
    "schema": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "页面标题"
            },
            "blocks": {
                "type": "array",
                "description": "Notion 块列表",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": [
                                "paragraph",
                                "heading_1",
                                "heading_2",
                                "heading_3",
                                "bulleted_list",
                                "numbered_list",
                                "code",
                                "divider",
                                "bookmark",
                                "callout",
                                "to_do"
                            ],
                            "description": "块类型"
                        },
                        "content": {
                            "type": "string",
                            "description": "文本内容（用于 paragraph, heading, code, callout, to_do）"
                        },
                        "items": {
                            "type": "array",
                            "description": "列表项（用于 bulleted_list, numbered_list）"
                        },
                        "language": {
                            "type": "string",
                            "description": "代码语言（用于 code 块）"
                        },
                        "checked": {
                            "type": "boolean",
                            "description": "是否勾选（用于 to_do 块）"
                        },
                        "url": {
                            "type": "string",
                            "description": "链接地址（用于 bookmark 块）"
                        },
                        "emoji": {
                            "type": "string",
                            "description": "表情符号（用于 callout 块）"
                        }
                    },
                    "required": ["type"],
                    "additionalProperties": True
                }
            }
        },
        "required": ["title", "blocks"],
        "additionalProperties": False
    }
}
