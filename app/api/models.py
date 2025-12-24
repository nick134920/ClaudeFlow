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
