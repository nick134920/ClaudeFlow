import os
import re
from fastapi import FastAPI, BackgroundTasks, Query
from pydantic import BaseModel
from dotenv import load_dotenv

from agent import run_summarize_agent

load_dotenv()

API_KEY = os.getenv("API_KEY")

app = FastAPI()


class SummarizeRequest(BaseModel):
    url: str


def is_valid_url(url: str) -> bool:
    """简单的 URL 格式验证"""
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url))


@app.post("/summarize")
async def summarize(
    request: SummarizeRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Query(..., description="API Key")
):
    # 验证 API Key
    if api_key != API_KEY:
        return {"success": False}

    # 验证 URL 格式
    if not is_valid_url(request.url):
        return {"success": False}

    # 添加后台任务
    background_tasks.add_task(run_summarize_agent, request.url)

    return {"success": True}
