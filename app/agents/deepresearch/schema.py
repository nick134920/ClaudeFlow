"""DeepResearch Agent 输出 JSON Schema 定义"""

# Notion 输出的 JSON Schema
# 用于 Claude Agent SDK 的 output_format 参数，强制结构化输出
NOTION_OUTPUT_SCHEMA = {
    "type": "json_schema",
    "schema": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "报告标题"
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
                                "to_do"
                            ],
                            "description": "块类型"
                        },
                        "content": {
                            "type": "string",
                            "description": "文本内容（用于 paragraph, heading, code, to_do）"
                        },
                        "items": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "列表项（用于 bulleted_list, numbered_list）"
                        },
                        "language": {
                            "type": "string",
                            "description": "代码语言（用于 code 块）"
                        },
                        "checked": {
                            "type": "boolean",
                            "description": "是否勾选（用于 to_do 块）"
                        }
                    },
                    "required": ["type"],
                    "additionalProperties": False
                }
            }
        },
        "required": ["title", "blocks"],
        "additionalProperties": False
    }
}
