# Claude Agent SDK output_format 编写指南

## 概述

`output_format` 是 Claude Agent SDK 提供的结构化输出功能，通过 JSON Schema 约束模型输出格式，确保返回的数据结构符合预期。

## 基本用法

```python
from claude_agent_sdk import ClaudeAgentOptions, query, ResultMessage

schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "score": {"type": "number"}
    },
    "required": ["name", "score"]
}

options = ClaudeAgentOptions(
    output_format={
        "type": "json_schema",
        "schema": schema
    }
)

async for message in query(prompt="分析这段文本", options=options):
    if isinstance(message, ResultMessage):
        # structured_output 是已验证的 JSON 对象
        print(message.structured_output)
```

## output_format 结构

```python
output_format = {
    "type": "json_schema",  # 固定值
    "schema": {
        # 标准 JSON Schema 定义
    }
}
```

## JSON Schema 支持的约束

### 基本类型

| 类型 | 说明 | 示例 |
|------|------|------|
| `string` | 字符串 | `{"type": "string"}` |
| `number` | 数字（含小数） | `{"type": "number"}` |
| `integer` | 整数 | `{"type": "integer"}` |
| `boolean` | 布尔值 | `{"type": "boolean"}` |
| `array` | 数组 | `{"type": "array", "items": {...}}` |
| `object` | 对象 | `{"type": "object", "properties": {...}}` |

### 常用约束

```python
# 字符串枚举
{
    "type": "string",
    "enum": ["positive", "negative", "neutral"]
}

# 数字范围
{
    "type": "number",
    "minimum": 0,
    "maximum": 100
}

# 数组长度
{
    "type": "array",
    "items": {"type": "string"},
    "minItems": 3,
    "maxItems": 7
}

# 必填字段
{
    "type": "object",
    "properties": {...},
    "required": ["field1", "field2"]
}

# 禁止额外属性
{
    "type": "object",
    "properties": {...},
    "additionalProperties": False
}
```

### 嵌套对象

```python
{
    "type": "object",
    "properties": {
        "user": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name"]
        }
    }
}
```

### 复杂数组

```python
{
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "module": {"type": "string"},
            "children": {
                "type": "array",
                "items": {"type": "string"}
            }
        },
        "required": ["module", "children"]
    }
}
```

## 设计原则

### 1. 使用具体字段而非自由数组

**问题**: JSON Schema 无法约束数组元素的顺序或特定位置的内容。

```python
# ❌ 不推荐：自由数组方式
{
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "blocks": {
            "type": "array",
            "items": {"type": "object"}  # 模型可以自由决定内容
        }
    }
}

# ✅ 推荐：具体字段方式
{
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "overview": {"type": "string"},
        "key_points": {"type": "array", "items": {"type": "string"}},
        "summary": {"type": "string"}
    },
    "required": ["title", "overview", "key_points", "summary"]
}
```

### 2. Schema 约束结构，Prompt 指导内容

| 组件 | 作用 |
|------|------|
| Schema | 定义字段名称、类型、必填项 |
| Prompt | 指导字段应该填什么内容 |

```python
# Schema 定义结构
schema = {
    "properties": {
        "summary": {
            "type": "string",
            "description": "文章摘要"  # description 提供提示
        }
    }
}

# Prompt 指导内容
prompt = """
分析文章并返回 JSON：
{
  "summary": "200-300字的详细摘要，包含主要观点..."
}
"""
```

### 3. 使用 description 增强提示

```python
{
    "type": "object",
    "properties": {
        "title": {
            "type": "string",
            "description": "页面标题，格式: 项目名称-中文标题-日期"
        },
        "key_points": {
            "type": "array",
            "description": "核心要点（5个）",
            "items": {"type": "string"},
            "minItems": 3,
            "maxItems": 7
        }
    }
}
```

### 4. 需要特定格式时使用转换层

当最终输出需要特定格式（如 Notion blocks）时，使用转换函数：

```python
# Schema 输出结构化数据
GITHUB_OUTPUT_SCHEMA = {
    "schema": {
        "properties": {
            "title": {"type": "string"},
            "overview": {"type": "string"},
            "key_points": {"type": "array", "items": {"type": "string"}}
        }
    }
}

# 转换函数
def github_output_to_blocks(data: dict) -> dict:
    """将结构化输出转换为 blocks 格式"""
    blocks = [
        {"type": "heading_1", "content": "项目概述"},
        {"type": "paragraph", "content": data["overview"]},
        {"type": "heading_1", "content": "核心要点"},
        {"type": "bulleted_list", "items": data["key_points"]}
    ]
    return {"title": data["title"], "blocks": blocks}

# 处理输出
async def process_structured_output(self, structured_output: dict):
    data = github_output_to_blocks(structured_output)
    self._write_to_notion(data)
```

## 完整示例

### GitHub 项目分析 Schema

```python
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
                    "stars": {"type": "integer"},
                    "forks": {"type": "integer"},
                    "last_commit": {"type": "string"}
                },
                "required": ["stars", "forks", "last_commit"]
            },
            "overview": {
                "type": "string",
                "description": "项目概述（100-200字）"
            },
            "key_points": {
                "type": "array",
                "description": "核心要点",
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
                "description": "核心模块结构",
                "items": {
                    "type": "object",
                    "properties": {
                        "module": {"type": "string"},
                        "children": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["module", "children"]
                }
            },
            "deployment": {
                "type": "object",
                "properties": {
                    "requirements": {"type": "string"},
                    "install_steps": {"type": "string"},
                    "start_command": {"type": "string"}
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
```

### 对应的 Prompt

```python
def get_github_prompt(url: str) -> str:
    return f"""
分析 GitHub 仓库：{url}

返回以下 JSON 结构：
{{
  "title": "项目名称-中文标题-{current_date}",
  "url": "{url}",
  "stats": {{
    "stars": 1234,
    "forks": 567,
    "last_commit": "2024-01-01"
  }},
  "overview": "项目概述...",
  "key_points": ["要点1", "要点2", "要点3"],
  "detailed_summary": "详细总结...",
  "architecture": [
    {{"module": "模块1", "children": ["子模块1", "子模块2"]}}
  ],
  "deployment": {{
    "requirements": "Node.js >= 18",
    "install_steps": "npm install",
    "start_command": "npm start"
  }},
  "task_time": "{current_time}"
}}
"""
```

## 处理结构化输出

```python
from claude_agent_sdk import ResultMessage

async for message in query(prompt=prompt, options=options):
    if isinstance(message, ResultMessage):
        if message.structured_output:
            # 结构化输出可用
            data = message.structured_output
            process_data(data)
```

## 常见问题

### Q: Schema 能否强制数组元素顺序？
**A**: 不能。JSON Schema 只能约束数组元素类型和数量，无法约束顺序。需要使用具体字段替代。

### Q: 如何确保模型填写特定内容？
**A**: Schema 约束结构，Prompt 指导内容。在 `description` 中提供提示，在 Prompt 中给出示例。

### Q: additionalProperties 应该设为什么？
**A**: 推荐设为 `False`，防止模型输出未定义的字段。

### Q: minItems/maxItems 有效吗？
**A**: 有效，可以约束数组长度范围。

## 参考

- [Claude Agent SDK Python](https://github.com/anthropics/claude-agent-sdk-python)
- [JSON Schema 规范](https://json-schema.org/)
