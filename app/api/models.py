import re
from pydantic import BaseModel, field_validator


class NewProjectAnalyseRequest(BaseModel):
    """新项目分析请求模型"""
    url: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        if not re.match(pattern, v):
            raise ValueError("无效的 URL 格式")
        return v


class TaskResponse(BaseModel):
    """通用任务响应模型"""
    success: bool
    task_id: str | None = None
    message: str | None = None


class HealthCheckResponse(BaseModel):
    """Agent 健康检查响应模型"""
    healthy: bool
    response: str | None = None
    error: str | None = None


class DeepResearchRequest(BaseModel):
    """深度研究请求模型"""
    topic: str

    @field_validator("topic")
    @classmethod
    def validate_topic(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("研究主题至少需要 2 个字符")
        if len(v) > 500:
            raise ValueError("研究主题不能超过 500 个字符")
        return v
