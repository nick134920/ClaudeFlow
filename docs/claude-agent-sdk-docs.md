# Claude Agent SDK 中文文档

> 来源: https://platform.claude.com/docs/zh-CN/agent-sdk/

---

## 目录

1. [Agent SDK 概览](#agent-sdk-概览)
2. [快速入门](#快速入门)
3. [Python SDK 参考](#python-sdk-参考)
4. [TypeScript SDK 参考](#typescript-sdk-参考)
5. [SDK 中的 MCP](#sdk-中的-mcp)
6. [自定义工具](#自定义工具)
7. [处理权限](#处理权限)
8. [使用钩子控制执行](#使用钩子控制执行)
9. [会话管理](#会话管理)
10. [SDK 中的子代理](#sdk-中的子代理)
11. [托管 Agent SDK](#托管-agent-sdk)
12. [安全部署 AI 代理](#安全部署-ai-代理)
13. [流式输入模式 vs 单消息输入模式](#流式输入模式-vs-单消息输入模式)
14. [跟踪成本和使用情况](#跟踪成本和使用情况)
15. [SDK 中的 Agent Skills](#sdk-中的-agent-skills)
16. [SDK 中的插件](#sdk-中的插件)
17. [修改系统提示词](#修改系统提示词)
18. [SDK 中的结构化输出](#sdk-中的结构化输出)
19. [SDK 中的斜杠命令](#sdk-中的斜杠命令)
20. [待办事项列表](#待办事项列表)
21. [文件检查点](#文件检查点)
22. [迁移指南](#迁移指南)
23. [TypeScript V2 预览版](#typescript-v2-预览版)

---

# Agent SDK 概览

Claude Agent SDK 是一个可编程接口，用于 Claude Code 的代理功能，使您能够在您自己的应用程序中构建 AI 代理。借助该 SDK，您可以创建能够执行以下操作的代理：

- 理解具有复杂上下文的多步骤指令
- 使用内置工具和通过 MCP 的外部工具执行操作
- 在代理循环中运行，进行连续操作直到完成任务
- 保持会话状态以进行长时间运行的交互

该 SDK 提供 Python 和 TypeScript 两种版本，为构建从简单自动化到复杂自主工作流的各种代理提供了灵活的平台。

## 核心能力

### 代理循环

SDK 实现了一个代理循环，Claude 在其中持续处理任务直到完成。与返回单一响应的传统 API 调用不同，代理循环允许 Claude：

1. 分析当前任务状态
2. 决定采取哪些操作
3. 执行操作（使用工具）
4. 评估结果
5. 继续或完成任务

这种循环模式使 Claude 能够处理复杂的多步骤任务，例如：

- 跨多个文件进行代码重构
- 运行和迭代测试直到通过
- 构建具有多个组件的功能

### 内置工具

SDK 提供了一组针对软件开发任务优化的内置工具：

| 工具 | 描述 |
|------|------|
| Read | 从文件系统读取文件 |
| Write | 创建或覆盖具有指定内容的文件 |
| Edit | 对现有文件进行有针对性的编辑 |
| Bash | 在持久的 shell 会话中执行命令 |
| Glob | 使用模式匹配搜索文件名 |
| Grep | 在文件内容中搜索模式 |
| LS | 列出目录内容 |
| WebFetch | 获取并处理网页内容 |
| WebSearch | 使用 Claude 搜索网页 |
| TodoRead/TodoWrite | 管理任务列表 |
| NotebookEdit | 编辑 Jupyter 笔记本单元格 |

这些工具提供了与 Claude Code 交互式环境相同的核心能力，允许代理有效地处理代码和文件。

### 外部工具（MCP）

除了内置工具外，SDK 还支持模型上下文协议 (MCP) 用于集成外部工具和服务。

MCP 允许您：

- 连接到数据库、API 和其他服务
- 创建具有特定领域能力的自定义工具
- 在代理之间共享工具配置

有关在 SDK 中设置 MCP 服务器的详细信息，请参阅 MCP 指南。

## 安装

### 前提条件

- 有效的 Anthropic API 密钥
- Claude Code CLI（使用 `npm install -g @anthropic-ai/claude-code` 安装）
- Node.js 18+（用于 TypeScript）或 Python 3.10+（用于 Python）

### TypeScript 安装

```bash
npm install @anthropic-ai/claude-agent-sdk
```

### Python 安装

```bash
pip install claude-agent-sdk
```

## 基本用法

### TypeScript

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

// 简单的单次查询
for await (const message of query({
  prompt: "What is 2 + 2?",
  options: { maxTurns: 1 }
})) {
  if (message.type === "assistant") {
    console.log(message.message);
  }
}
```

### Python

```python
import asyncio
from claude_agent_sdk import query

async def main():
    async for message in query(prompt="What is 2 + 2?", max_turns=1):
        if message.type == "assistant":
            print(message.message)

asyncio.run(main())
```

---

# 快速入门

本指南向您展示如何使用 Claude Agent SDK 创建一个代理，该代理可以读取文件并建议对代码库的改进。

## 前提条件

开始之前，请确保您已：

- Claude Pro、Max 或 Teams 订阅
- 安装了 Claude Code CLI（版本 1.0.33 或更高）
- Node.js 18+（用于 TypeScript）或 Python 3.10+（用于 Python）
- 您系统上的终端访问权限

## 环境设置

### 步骤 1：设置 API 密钥

SDK 需要使用您的 Anthropic API 密钥进行身份验证。您可以在终端中设置它：

```bash
export ANTHROPIC_API_KEY=your-api-key
```

### 步骤 2：安装 Claude Code CLI

SDK 需要 Claude Code CLI。使用 npm 全局安装：

```bash
npm install -g @anthropic-ai/claude-code
```

安装后验证：

```bash
claude --version
```

### 步骤 3：安装 Claude Agent SDK

**TypeScript：**

```bash
npm install @anthropic-ai/claude-agent-sdk
```

**Python：**

```bash
pip install claude-agent-sdk
```

## 构建您的第一个代理

让我们构建一个读取文件并建议如何修复其中错误的代理。

### TypeScript

创建一个名为 `agent.ts` 的文件：

```typescript
import { query, type MessageStream } from "@anthropic-ai/claude-agent-sdk";

const prompt = `Read the file main.py and suggest how to fix any bugs you find.`;

async function main() {
  const messageStream: MessageStream = query({
    prompt,
    options: {
      maxTurns: 10,
      systemPrompt:
        "You are a helpful coding assistant that analyzes code and suggests improvements.",
    },
  });

  for await (const message of messageStream) {
    if (message.type === "assistant") {
      const textContent = message.message.content
        .filter((block): block is { type: "text"; text: string } =>
          block.type === "text"
        )
        .map((block) => block.text)
        .join("");

      if (textContent) {
        console.log("Claude:", textContent);
      }
    }
  }
}

main();
```

### Python

创建一个名为 `agent.py` 的文件：

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage

PROMPT = "Read the file main.py and suggest how to fix any bugs you find."

async def main():
    options = ClaudeAgentOptions(
        max_turns=10,
        system_prompt="You are a helpful coding assistant that analyzes code and suggests improvements."
    )

    async for message in query(prompt=PROMPT, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.message.content:
                if hasattr(block, 'text'):
                    print(f"Claude: {block.text}")

asyncio.run(main())
```

## 运行代理

创建一个带有 bug 的测试文件 `main.py`：

```python
def calculate_average(numbers):
    total = 0
    for num in numbers:
        total += num
    return total / len(numbers)  # Bug: no check for empty list

result = calculate_average([])
print(f"Average: {result}")
```

运行代理：

**TypeScript：**

```bash
npx ts-node agent.ts
```

**Python：**

```bash
python agent.py
```

---

# Python SDK 参考

## 安装

```bash
pip install claude-agent-sdk
```

## 基本用法

### 简单查询

```python
import asyncio
from claude_agent_sdk import query

async def main():
    async for message in query(
        prompt="What files are in the current directory?"
    ):
        if message.type == "assistant":
            print(message.message)

asyncio.run(main())
```

### 使用选项配置

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    options = ClaudeAgentOptions(
        max_turns=5,
        system_prompt="You are a helpful assistant."
    )

    async for message in query(
        prompt="Explain what this codebase does",
        options=options
    ):
        if message.type == "assistant":
            print(message.message)

asyncio.run(main())
```

## ClaudeAgentOptions 类

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `model` | `str` | `None` | 要使用的 Claude 模型 |
| `max_turns` | `int` | 无限 | 代理循环的最大轮次 |
| `system_prompt` | `str \| dict` | `None` | 自定义系统提示或预设 |
| `cwd` | `str` | 当前目录 | 工作目录 |
| `permission_mode` | `str` | `"default"` | 工具权限模式 |
| `allowed_tools` | `list[str]` | 全部 | 允许的工具列表 |
| `mcp_servers` | `dict` | `None` | MCP 服务器配置 |
| `env` | `dict` | `None` | 环境变量 |
| `resume` | `str` | `None` | 会话 ID 以恢复 |

## 消息类型

SDK 通过异步迭代器生成各种消息类型：

```python
from claude_agent_sdk import (
    AssistantMessage,
    UserMessage,
    SystemMessage,
    ResultMessage,
    ToolUseMessage,
    ToolResultMessage,
)
```

### AssistantMessage

Claude 的响应消息：

```python
async for message in query(prompt="Hello"):
    if isinstance(message, AssistantMessage):
        for block in message.message.content:
            if hasattr(block, 'text'):
                print(block.text)
```

### ResultMessage

代理完成时的最终结果：

```python
async for message in query(prompt="Calculate 2+2"):
    if isinstance(message, ResultMessage):
        print(f"Result: {message.result}")
        print(f"Session ID: {message.session_id}")
```

---

# TypeScript SDK 参考

## 安装

```bash
npm install @anthropic-ai/claude-agent-sdk
```

## 基本用法

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "What files are in the current directory?"
})) {
  if (message.type === "assistant") {
    console.log(message.message);
  }
}
```

## query() 函数

```typescript
function query(params: {
  prompt: string | AsyncIterable<UserMessage>;
  options?: Options;
}): AsyncGenerator<SDKMessage>;
```

## Options 接口

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `model` | `string` | `undefined` | 要使用的 Claude 模型 |
| `maxTurns` | `number` | `Infinity` | 最大代理轮次 |
| `systemPrompt` | `string \| SystemPromptConfig` | `undefined` | 自定义系统提示 |
| `cwd` | `string` | `process.cwd()` | 工作目录 |
| `permissionMode` | `PermissionMode` | `"default"` | 工具权限模式 |
| `allowedTools` | `string[]` | 全部 | 允许的工具 |
| `mcpServers` | `Record<string, McpServerConfig>` | `undefined` | MCP 服务器 |
| `env` | `Record<string, string>` | `undefined` | 环境变量 |
| `resume` | `string` | `undefined` | 恢复会话 ID |

## 消息类型

```typescript
type SDKMessage =
  | SystemMessage
  | AssistantMessage
  | UserMessage
  | ResultMessage;

interface AssistantMessage {
  type: "assistant";
  session_id: string;
  message: {
    role: "assistant";
    content: ContentBlock[];
  };
}

interface ResultMessage {
  type: "result";
  session_id: string;
  result: string;
  cost_usd: number;
  is_error: boolean;
  duration_ms: number;
  num_turns: number;
}
```

---

# SDK 中的 MCP

模型上下文协议 (MCP) 允许您使用标准化协议将外部工具和服务连接到 Claude。

## 配置 MCP 服务器

### TypeScript

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "What's the current time?",
  options: {
    mcpServers: {
      time: {
        command: "npx",
        args: ["-y", "@anthropic-ai/mcp-server-time"],
      },
    },
  },
})) {
  if (message.type === "assistant") {
    console.log(message.message);
  }
}
```

### Python

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    options = ClaudeAgentOptions(
        mcp_servers={
            "time": {
                "command": "npx",
                "args": ["-y", "@anthropic-ai/mcp-server-time"],
            },
        },
    )

    async for message in query(
        prompt="What's the current time?",
        options=options
    ):
        if message.type == "assistant":
            print(message.message)

asyncio.run(main())
```

## MCP 服务器配置选项

| 参数 | 类型 | 描述 |
|------|------|------|
| `command` | `string` | 运行服务器的命令 |
| `args` | `string[]` | 命令参数 |
| `env` | `Record<string, string>` | 环境变量 |
| `cwd` | `string` | 服务器工作目录 |

---

# 自定义工具

自定义工具允许您定义 Claude 可以使用的新功能，从而扩展其能力。

## 定义工具

### TypeScript

```typescript
import { query, tool } from "@anthropic-ai/claude-agent-sdk";

// 定义自定义工具
const weatherTool = tool({
  name: "get_weather",
  description: "获取指定城市的天气信息",
  schema: {
    type: "object",
    properties: {
      city: { type: "string", description: "城市名称" },
    },
    required: ["city"],
  },
  handler: async ({ city }) => {
    // 实际实现会调用天气 API
    return { temperature: 22, condition: "晴天" };
  },
});

for await (const message of query({
  prompt: "北京的天气怎么样？",
  options: {
    customTools: [weatherTool],
  },
})) {
  if (message.type === "assistant") {
    console.log(message.message);
  }
}
```

### Python

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def get_weather(city: str) -> dict:
    return {"temperature": 22, "condition": "晴天"}

WEATHER_TOOL = {
    "name": "get_weather",
    "description": "获取指定城市的天气信息",
    "input_schema": {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "城市名称"}
        },
        "required": ["city"]
    },
    "handler": get_weather
}

async def main():
    options = ClaudeAgentOptions(
        custom_tools=[WEATHER_TOOL]
    )

    async for message in query(
        prompt="北京的天气怎么样？",
        options=options
    ):
        if message.type == "assistant":
            print(message.message)

asyncio.run(main())
```

---

# 处理权限

SDK 提供多种方式来控制 Claude 可以执行哪些操作。

## 权限模式

| 模式 | 描述 |
|------|------|
| `"default"` | 默认行为，某些工具需要确认 |
| `"acceptEdits"` | 自动批准文件编辑 |
| `"bypassPermissions"` | 跳过所有权限检查（危险） |

### 配置权限模式

**TypeScript：**

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "重构 main.py 文件",
  options: {
    permissionMode: "acceptEdits",
  },
})) {
  // 处理消息
}
```

**Python：**

```python
options = ClaudeAgentOptions(
    permission_mode="acceptEdits"
)
```

## canUseTool 回调

使用 `canUseTool` 回调实现自定义权限逻辑：

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "执行一些文件操作",
  options: {
    canUseTool: async (tool, input) => {
      // 自定义权限逻辑
      if (tool === "Bash" && input.command.includes("rm")) {
        return false; // 拒绝删除命令
      }
      return true; // 允许其他操作
    },
  },
})) {
  // 处理消息
}
```

---

# 使用钩子控制执行

钩子允许您拦截和控制代理执行的各个方面。

## 钩子类型

| 钩子 | 触发时机 |
|------|----------|
| `PreToolUse` | 工具执行前 |
| `PostToolUse` | 工具执行后 |
| `UserPromptSubmit` | 用户提示提交时 |

## 配置钩子

钩子在 Claude 设置中配置：

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "command": "echo 'Bash command: $INPUT' >> /tmp/audit.log"
      }
    ],
    "PostToolUse": [
      {
        "matcher": "*",
        "command": "echo 'Tool completed: $TOOL_NAME'"
      }
    ]
  }
}
```

## 钩子环境变量

钩子命令可以访问以下环境变量：

| 变量 | 描述 |
|------|------|
| `$TOOL_NAME` | 工具名称 |
| `$INPUT` | 工具输入（JSON） |
| `$OUTPUT` | 工具输出（仅 PostToolUse） |
| `$SESSION_ID` | 当前会话 ID |

---

# 会话管理

会话允许您维护跨多次交互的对话上下文。

## 恢复会话

### TypeScript

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

// 保存会话 ID
let sessionId: string;

// 第一次交互
for await (const message of query({ prompt: "记住数字 42" })) {
  if (message.type === "result") {
    sessionId = message.session_id;
  }
}

// 恢复会话
for await (const message of query({
  prompt: "我之前让你记住的数字是什么？",
  options: { resume: sessionId },
})) {
  if (message.type === "assistant") {
    console.log(message.message);
  }
}
```

### Python

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

async def main():
    session_id = None

    # 第一次交互
    async for message in query(prompt="记住数字 42"):
        if isinstance(message, ResultMessage):
            session_id = message.session_id

    # 恢复会话
    options = ClaudeAgentOptions(resume=session_id)
    async for message in query(
        prompt="我之前让你记住的数字是什么？",
        options=options
    ):
        if message.type == "assistant":
            print(message.message)

asyncio.run(main())
```

## 会话分叉

会话分叉允许您从现有会话创建分支：

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "继续之前的任务",
  options: {
    resume: sessionId,
    forkSession: true, // 创建新分支而不是修改原会话
  },
})) {
  // 处理消息
}
```

---

# SDK 中的子代理

子代理是专门化的 AI 代理，可以被编排来处理复杂任务。

## 配置子代理

子代理通过 markdown 文件在 `.claude/agents/` 目录中配置：

创建 `.claude/agents/code-reviewer.md`：

```markdown
---
name: code-reviewer
description: 专门进行代码审查的代理
allowed-tools: Read, Grep, Glob
model: claude-sonnet-4-5
---

你是一个代码审查专家。请仔细审查代码，关注：
1. 代码质量和可读性
2. 潜在的 bug
3. 安全问题
4. 性能优化建议
```

## 使用子代理

子代理会自动通过 Task 工具可用：

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "使用 code-reviewer 子代理审查 src/ 目录下的代码",
  options: {
    maxTurns: 10,
  },
})) {
  if (message.type === "assistant") {
    console.log(message.message);
  }
}
```

---

# 托管 Agent SDK

在生产环境中部署 Agent SDK 时的考虑事项。

## 环境配置

### 必需的环境变量

```bash
export ANTHROPIC_API_KEY=your-api-key
export CLAUDE_CODE_USE_BEDROCK=1  # 可选：使用 AWS Bedrock
export AWS_REGION=us-east-1       # 如果使用 Bedrock
```

### Docker 部署

```dockerfile
FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
RUN npm install

COPY . .

# 安装 Claude Code CLI
RUN npm install -g @anthropic-ai/claude-code

ENV ANTHROPIC_API_KEY=""
CMD ["node", "dist/index.js"]
```

## 扩展考虑

- **并发限制**：控制并发会话数量
- **超时设置**：为长时间运行的任务设置适当的超时
- **错误处理**：实现重试逻辑和优雅降级
- **监控**：跟踪 API 使用量和成本

---

# 安全部署 AI 代理

在生产环境中安全部署 AI 代理的最佳实践。

## 隔离策略

### 沙箱执行

使用沙箱模式限制代理可以执行的操作：

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "分析这段代码",
  options: {
    sandboxMode: true,
    allowedTools: ["Read", "Grep", "Glob"], // 仅允许只读工具
  },
})) {
  // 处理消息
}
```

### 工作目录限制

限制代理只能访问特定目录：

```typescript
options: {
  cwd: "/safe/working/directory",
  // 代理只能在此目录内操作
}
```

## 凭证管理

- **不要在提示中包含敏感信息**
- **使用环境变量传递 API 密钥**
- **定期轮换凭证**
- **使用最小权限原则**

## 审计日志

记录所有代理操作以便审计：

```typescript
options: {
  hooks: {
    PostToolUse: [
      {
        matcher: "*",
        command: "echo '$TOOL_NAME: $INPUT' >> /var/log/agent-audit.log"
      }
    ]
  }
}
```

---

# 流式输入模式 vs 单消息输入模式

SDK 支持两种输入模式，适用于不同的使用场景。

## 单消息输入模式

适用于简单的单轮交互：

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

// 简单的字符串提示
for await (const message of query({
  prompt: "Hello, Claude!",
})) {
  // 处理响应
}
```

## 流式输入模式

适用于需要动态发送多条消息的场景：

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

async function* inputStream() {
  yield {
    type: "user",
    message: { role: "user", content: [{ type: "text", text: "第一条消息" }] },
  };
  // 可以根据条件动态生成更多消息
  yield {
    type: "user",
    message: { role: "user", content: [{ type: "text", text: "第二条消息" }] },
  };
}

for await (const message of query({
  prompt: inputStream(),
})) {
  // 处理响应
}
```

### 何时使用流式输入

- 实现交互式对话
- 根据代理响应动态发送后续指令
- 处理需要多轮交互的复杂任务

---

# 跟踪成本和使用情况

监控和控制 API 使用成本。

## 获取成本信息

每个 `ResultMessage` 包含成本信息：

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({ prompt: "Hello" })) {
  if (message.type === "result") {
    console.log(`Cost: $${message.cost_usd}`);
    console.log(`Duration: ${message.duration_ms}ms`);
    console.log(`Turns: ${message.num_turns}`);
  }
}
```

## 设置成本限制

使用 `maxTurns` 控制最大轮次以限制成本：

```typescript
options: {
  maxTurns: 10, // 最多 10 轮交互
}
```

## 使用跟踪

```python
import asyncio
from claude_agent_sdk import query, ResultMessage

async def main():
    total_cost = 0

    async for message in query(prompt="执行复杂任务"):
        if isinstance(message, ResultMessage):
            total_cost += message.cost_usd
            print(f"本次成本: ${message.cost_usd}")
            print(f"累计成本: ${total_cost}")

asyncio.run(main())
```

---

# SDK 中的 Agent Skills

Agent Skills 是预定义的能力模块，可以增强代理的功能。

## 技能文件结构

技能定义为 markdown 文件，位于 `.claude/skills/` 目录：

```markdown
---
name: database-admin
description: 数据库管理技能
allowed-tools: Bash, Read, Write
---

你是一个数据库管理专家。你可以：
- 执行 SQL 查询
- 优化数据库性能
- 管理数据库备份
```

## 使用技能

技能会自动加载并可用于代理：

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "/database-admin 优化查询性能",
  options: {
    settingSources: ["project"], // 加载项目技能
  },
})) {
  // 处理响应
}
```

---

# SDK 中的插件

插件扩展了 SDK 的功能，提供额外的工具和能力。

## 插件配置

在 `.claude/settings.json` 中配置插件：

```json
{
  "plugins": {
    "my-plugin": {
      "enabled": true,
      "config": {
        "option1": "value1"
      }
    }
  }
}
```

## 创建自定义插件

插件是 npm 包，遵循特定的接口规范：

```typescript
// my-plugin/index.ts
export default {
  name: "my-plugin",
  version: "1.0.0",
  tools: [
    {
      name: "custom_tool",
      description: "自定义工具",
      schema: {
        type: "object",
        properties: {},
      },
      handler: async () => {
        return { result: "success" };
      },
    },
  ],
};
```

---

# 修改系统提示词

自定义 Claude 的行为和响应风格。

## 使用自定义系统提示

### TypeScript

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "帮我写代码",
  options: {
    systemPrompt: "你是一个专业的 Python 开发者，专注于数据科学领域。",
  },
})) {
  // 处理响应
}
```

### Python

```python
options = ClaudeAgentOptions(
    system_prompt="你是一个专业的 Python 开发者，专注于数据科学领域。"
)
```

## 使用预设系统提示

使用 Claude Code 的默认系统提示：

```typescript
options: {
  systemPrompt: {
    type: "preset",
    preset: "claude_code"
  }
}
```

## 添加额外指令

在现有系统提示基础上添加指令：

```typescript
options: {
  systemPrompt: {
    type: "preset",
    preset: "claude_code",
    additionalInstructions: "始终使用中文回复。"
  }
}
```

---

# SDK 中的结构化输出

使用 JSON Schema 获取结构化的响应。

## 定义输出模式

### TypeScript

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

const schema = {
  type: "object",
  properties: {
    summary: { type: "string" },
    issues: {
      type: "array",
      items: {
        type: "object",
        properties: {
          severity: { type: "string", enum: ["low", "medium", "high"] },
          description: { type: "string" },
          line: { type: "number" },
        },
        required: ["severity", "description"],
      },
    },
  },
  required: ["summary", "issues"],
};

for await (const message of query({
  prompt: "分析 main.py 的代码质量",
  options: {
    outputSchema: schema,
  },
})) {
  if (message.type === "result") {
    const result = JSON.parse(message.result);
    console.log(`Summary: ${result.summary}`);
    console.log(`Found ${result.issues.length} issues`);
  }
}
```

### Python

```python
schema = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "issues": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "severity": {"type": "string"},
                    "description": {"type": "string"}
                }
            }
        }
    },
    "required": ["summary", "issues"]
}

options = ClaudeAgentOptions(
    output_schema=schema
)
```

---

# SDK 中的斜杠命令

斜杠命令提供了一种使用以 `/` 开头的特殊命令来控制 Claude Code 会话的方法。

## 内置斜杠命令

| 命令 | 描述 |
|------|------|
| `/compact` | 压缩对话历史 |
| `/clear` | 清除对话历史 |
| `/help` | 显示帮助信息 |

## 使用斜杠命令

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

// 压缩对话历史
for await (const message of query({
  prompt: "/compact",
  options: { maxTurns: 1 },
})) {
  if (message.type === "system" && message.subtype === "compact_boundary") {
    console.log("压缩完成");
    console.log(`压缩前令牌数: ${message.compact_metadata.pre_tokens}`);
  }
}
```

## 创建自定义斜杠命令

在 `.claude/commands/` 目录创建 markdown 文件：

创建 `.claude/commands/refactor.md`：

```markdown
---
allowed-tools: Read, Edit, Write
description: 重构代码
---

重构选定的代码以提高可读性和可维护性。
关注代码整洁原则和最佳实践。
```

使用自定义命令：

```typescript
for await (const message of query({
  prompt: "/refactor src/main.ts",
  options: { maxTurns: 5 },
})) {
  // 处理响应
}
```

---

# 待办事项列表

待办事项跟踪提供了一种结构化的方式来管理任务并向用户显示进度。

## 监控待办事项变化

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "优化我的 React 应用性能并使用待办事项跟踪进度",
  options: { maxTurns: 15 },
})) {
  if (message.type === "tool_use" && message.name === "TodoWrite") {
    const todos = message.input.todos;

    console.log("待办事项状态更新：");
    todos.forEach((todo, index) => {
      const status =
        todo.status === "completed"
          ? "✅"
          : todo.status === "in_progress"
          ? "🔧"
          : "❌";
      console.log(`${index + 1}. ${status} ${todo.content}`);
    });
  }
}
```

## 待办事项状态

| 状态 | 描述 |
|------|------|
| `pending` | 任务待处理 |
| `in_progress` | 任务进行中 |
| `completed` | 任务已完成 |

---

# 文件检查点

文件检查点跟踪在代理会话期间通过 Write、Edit 和 NotebookEdit 工具所做的文件修改，允许您将文件回退到任何先前状态。

## 启用检查点

### TypeScript

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "重构认证模块",
  options: {
    enableFileCheckpointing: true,
    permissionMode: "acceptEdits",
    extraArgs: { "replay-user-messages": null },
  },
})) {
  // 处理响应并保存检查点 UUID
}
```

### Python

```python
options = ClaudeAgentOptions(
    enable_file_checkpointing=True,
    permission_mode="acceptEdits",
    extra_args={"replay-user-messages": None},
    env={**os.environ, "CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING": "1"}
)
```

## 回退文件

```typescript
// 恢复会话并回退
await using session = unstable_v2_resumeSession(sessionId, {
  enableFileCheckpointing: true,
});

await session.send("");
for await (const message of session.receive()) {
  await session.rewindFiles(checkpointId);
  break;
}
```

## 检查点限制

| 限制 | 描述 |
|------|------|
| 仅 Write/Edit/NotebookEdit 工具 | Bash 命令的更改不被跟踪 |
| 相同会话 | 检查点与创建它们的会话关联 |
| 仅文件内容 | 目录操作不会被回退 |
| 本地文件 | 远程文件不被跟踪 |

---

# 迁移指南

从 Claude Code SDK 迁移到 Claude Agent SDK。

## 变更内容

| 方面 | 旧版本 | 新版本 |
|------|--------|--------|
| 包名称 (TS/JS) | `@anthropic-ai/claude-code` | `@anthropic-ai/claude-agent-sdk` |
| Python 包 | `claude-code-sdk` | `claude-agent-sdk` |
| 文档位置 | Claude Code 文档 | API 指南 → Agent SDK |

## TypeScript 迁移步骤

1. 卸载旧包：

```bash
npm uninstall @anthropic-ai/claude-code
```

2. 安装新包：

```bash
npm install @anthropic-ai/claude-agent-sdk
```

3. 更新导入：

```typescript
// 之前
import { query } from "@anthropic-ai/claude-code";

// 之后
import { query } from "@anthropic-ai/claude-agent-sdk";
```

## Python 迁移步骤

1. 卸载旧包：

```bash
pip uninstall claude-code-sdk
```

2. 安装新包：

```bash
pip install claude-agent-sdk
```

3. 更新导入和类型名称：

```python
# 之前
from claude_code_sdk import query, ClaudeCodeOptions

# 之后
from claude_agent_sdk import query, ClaudeAgentOptions
```

## 破坏性变更

### 系统提示不再是默认值

SDK 不再默认使用 Claude Code 的系统提示：

```typescript
// 要获得旧行为，显式请求 Claude Code 预设
const result = query({
  prompt: "Hello",
  options: {
    systemPrompt: { type: "preset", preset: "claude_code" },
  },
});
```

### 设置源不再默认加载

SDK 不再默认从文件系统设置读取：

```typescript
// 要获得旧行为
const result = query({
  prompt: "Hello",
  options: {
    settingSources: ["user", "project", "local"],
  },
});
```

---

# TypeScript V2 预览版

V2 接口是一个不稳定的预览版，提供简化的会话管理 API。

## 安装

```bash
npm install @anthropic-ai/claude-agent-sdk
```

## 基本用法

### 单次提示

```typescript
import { unstable_v2_prompt } from "@anthropic-ai/claude-agent-sdk";

const result = await unstable_v2_prompt("What is 2 + 2?", {
  model: "claude-sonnet-4-5-20250929",
});
console.log(result.result);
```

### 基本会话

```typescript
import { unstable_v2_createSession } from "@anthropic-ai/claude-agent-sdk";

await using session = unstable_v2_createSession({
  model: "claude-sonnet-4-5-20250929",
});

await session.send("Hello!");
for await (const msg of session.receive()) {
  if (msg.type === "assistant") {
    const text = msg.message.content
      .filter((block) => block.type === "text")
      .map((block) => block.text)
      .join("");
    console.log(text);
  }
}
```

### 多轮对话

```typescript
import { unstable_v2_createSession } from "@anthropic-ai/claude-agent-sdk";

await using session = unstable_v2_createSession({
  model: "claude-sonnet-4-5-20250929",
});

// 第一轮
await session.send("What is 5 + 3?");
for await (const msg of session.receive()) {
  // 处理响应
}

// 第二轮
await session.send("Multiply that by 2");
for await (const msg of session.receive()) {
  // 处理响应
}
```

### 会话恢复

```typescript
import {
  unstable_v2_createSession,
  unstable_v2_resumeSession,
} from "@anthropic-ai/claude-agent-sdk";

// 创建会话并获取 session ID
const session = unstable_v2_createSession({
  model: "claude-sonnet-4-5-20250929",
});

await session.send("Remember this number: 42");
let sessionId;
for await (const msg of session.receive()) {
  sessionId = msg.session_id;
}
session.close();

// 恢复会话
await using resumedSession = unstable_v2_resumeSession(sessionId, {
  model: "claude-sonnet-4-5-20250929",
});

await resumedSession.send("What number did I ask you to remember?");
for await (const msg of resumedSession.receive()) {
  // 处理响应
}
```

## V2 API 参考

### `unstable_v2_createSession()`

创建新会话：

```typescript
function unstable_v2_createSession(options: {
  model: string;
}): Session;
```

### `unstable_v2_resumeSession()`

恢复现有会话：

```typescript
function unstable_v2_resumeSession(
  sessionId: string,
  options: { model: string }
): Session;
```

### `unstable_v2_prompt()`

单次查询便利函数：

```typescript
function unstable_v2_prompt(
  prompt: string,
  options: { model: string }
): Promise<Result>;
```

### Session 接口

```typescript
interface Session {
  send(message: string): Promise<void>;
  receive(): AsyncGenerator<SDKMessage>;
  close(): void;
}
```

---

> 文档生成日期: 2025-12-22
> 来源: https://platform.claude.com/docs/zh-CN/agent-sdk/
