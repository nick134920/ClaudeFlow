from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(
    title="Agent API",
    description="工程化的 Agent 服务接口",
    version="1.0.0",
)

# 注册路由
app.include_router(router)
