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
            "core_features": {
                "type": "array",
                "description": "核心功能列表，完整列出项目的所有主要功能",
                "items": {"type": "string"},
                "minItems": 5,
                "maxItems": 15
            },
            "tech_stack": {
                "type": "object",
                "description": "技术架构",
                "properties": {
                    "languages": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "编程语言"
                    },
                    "frameworks": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "框架和库"
                    },
                    "infrastructure": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "基础设施（数据库、缓存、消息队列等）"
                    },
                    "tools": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "构建工具和开发工具"
                    }
                },
                "required": ["languages", "frameworks"]
            },
            "architecture": {
                "type": "array",
                "description": "项目架构/模块结构",
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
            "key_config": {
                "type": "array",
                "description": "关键配置要素",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "配置项名称"},
                        "description": {"type": "string", "description": "配置说明"}
                    },
                    "required": ["name", "description"]
                }
            },
            "highlights": {
                "type": "array",
                "description": "项目亮点/设计特色",
                "items": {"type": "string"},
                "minItems": 3,
                "maxItems": 7
            },
            "key_commands": {
                "type": "array",
                "description": "关键命令",
                "items": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "命令"},
                        "description": {"type": "string", "description": "命令说明"}
                    },
                    "required": ["command", "description"]
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
            "title", "url", "stats", "overview", "core_features",
            "tech_stack", "architecture", "key_config", "highlights",
            "key_commands", "deployment", "task_time"
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

    # 技术架构文本
    tech_stack = data.get("tech_stack", {})
    tech_items = []
    if tech_stack.get("languages"):
        tech_items.append(f"语言: {', '.join(tech_stack['languages'])}")
    if tech_stack.get("frameworks"):
        tech_items.append(f"框架: {', '.join(tech_stack['frameworks'])}")
    if tech_stack.get("infrastructure"):
        tech_items.append(f"基础设施: {', '.join(tech_stack['infrastructure'])}")
    if tech_stack.get("tools"):
        tech_items.append(f"工具: {', '.join(tech_stack['tools'])}")

    # 关键配置
    key_config_items = [
        f"{item['name']}: {item['description']}"
        for item in data.get("key_config", [])
    ]

    # 关键命令
    key_commands_items = [
        f"`{item['command']}`: {item['description']}"
        for item in data.get("key_commands", [])
    ]

    blocks = [
        {"type": "bookmark", "url": data["url"]},
        {"type": "callout", "content": stats_text, "emoji": "📊"},
        {"type": "divider"},
        # 项目概述
        {"type": "heading_1", "content": "项目概述"},
        {"type": "paragraph", "content": data["overview"]},
        # 核心功能
        {"type": "heading_1", "content": "核心功能"},
        {"type": "bulleted_list", "items": data.get("core_features", [])},
        # 技术架构
        {"type": "heading_1", "content": "技术架构"},
        {"type": "bulleted_list", "items": tech_items},
        # 项目结构
        {"type": "heading_1", "content": "项目结构"},
        {"type": "bulleted_list", "items": [
            {"text": item["module"], "children": item["children"]}
            for item in data.get("architecture", [])
        ]},
        # 关键配置要素
        {"type": "heading_1", "content": "关键配置要素"},
        {"type": "bulleted_list", "items": key_config_items},
        # 项目亮点
        {"type": "heading_1", "content": "项目亮点"},
        {"type": "bulleted_list", "items": data.get("highlights", [])},
        # 关键命令
        {"type": "heading_1", "content": "关键命令"},
        {"type": "bulleted_list", "items": key_commands_items},
        # 部署说明
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
