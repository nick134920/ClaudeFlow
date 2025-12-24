from fastapi import APIRouter, BackgroundTasks, Query, Request
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock

from app.api.models import NewProjectAnalyseRequest, TaskResponse, HealthCheckResponse
from app.agents.newprojectanalyse.agent import run_newprojectanalyse_agent
from app.agents.newprojectanalyse.config import MODEL
from app.config import API_KEY
from app.core.logging import request_logger
from app.core.task_registry import task_registry

router = APIRouter()


def get_client_ip(request: Request) -> str:
    """获取客户端 IP"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/newprojectanalyse", response_model=TaskResponse)
async def newprojectanalyse(
    request: Request,
    body: NewProjectAnalyseRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Query(..., description="API Key"),
):
    """
    提交新项目分析任务

    - 验证 API Key
    - 验证 URL 格式
    - 提交后台任务
    - 返回任务 ID
    """
    client_ip = get_client_ip(request)
    path = "/newprojectanalyse"

    # 验证 API Key
    if api_key != API_KEY:
        request_logger.log(
            "WARNING", "POST", path, client_ip,
            status="rejected", extra={"reason": "invalid_api_key"}
        )
        return TaskResponse(success=False, message="Invalid API Key")

    # 生成任务 ID
    task_id = task_registry.generate_id("newprojectanalyse")

    # 记录请求日志
    request_logger.log(
        "INFO", "POST", path, client_ip,
        task_id=task_id, status="accepted"
    )

    # 添加后台任务
    background_tasks.add_task(run_newprojectanalyse_agent, body.url)

    return TaskResponse(success=True, task_id=task_id)


@router.get("/check-agent-health", response_model=HealthCheckResponse)
async def check_agent_health(
    request: Request,
    api_key: str = Query(..., description="API Key"),
):
    """
    Agent 健康检查

    - 验证 API Key
    - 实时调用 Agent SDK 测试连通性
    - 返回 Agent 响应或错误信息
    """
    client_ip = get_client_ip(request)
    path = "/check-agent-health"

    # 验证 API Key
    if api_key != API_KEY:
        request_logger.log(
            "WARNING", "GET", path, client_ip,
            status="rejected", extra={"reason": "invalid_api_key"}
        )
        return HealthCheckResponse(healthy=False, error="Invalid API Key")

    request_logger.log("INFO", "GET", path, client_ip, status="checking")

    try:
        # 使用简单配置调用 Agent SDK
        options = ClaudeAgentOptions(
            model=MODEL,
            max_turns=1,
            permission_mode="bypassPermissions",
        )

        response_text = ""
        async for message in query(prompt="what llm are you", options=options):
            if isinstance(message, AssistantMessage):
                blocks = getattr(message, "content", [])
                for block in blocks:
                    if isinstance(block, TextBlock):
                        text = getattr(block, "text", "")
                        if text:
                            response_text += text

        request_logger.log(
            "INFO", "GET", path, client_ip,
            status="healthy", extra={"response_length": len(response_text)}
        )
        return HealthCheckResponse(healthy=True, response=response_text)

    except Exception as e:
        error_msg = str(e)
        request_logger.log(
            "ERROR", "GET", path, client_ip,
            status="unhealthy", extra={"error": error_msg}
        )
        return HealthCheckResponse(healthy=False, error=error_msg)
