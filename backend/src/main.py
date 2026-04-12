"""
FastAPI 应用入口

日志文件切分服务的 REST API 主入口。
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.src.api.routes import router
from backend.src.db.session import init_db, create_tables
from backend.src.services.log_service import setup_logging, get_logger

# 初始化日志
setup_logging()
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("应用启动中...")

    # 初始化数据库
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/logfix_ai")
    init_db(database_url)
    logger.info(f"数据库连接初始化完成: {database_url}")

    # 创建表
    try:
        create_tables()
        logger.info("数据库表创建完成")
    except Exception as e:
        logger.error(f"数据库表创建失败: {e}")

    # 模型预加载
    try:
        from backend.src.services.ai_analyzer import init_client
        logger.info("模型预加载开始...")
        await init_client()
        logger.info("模型预加载完成, model=MiniMax-M2.7")
    except Exception as e:
        logger.error(f"模型预加载失败: {e}")

    yield

    # 关闭时
    try:
        from backend.src.services.ai_analyzer import close_client
        await close_client()
    except Exception as e:
        logger.error(f"关闭 OpenAI 客户端失败: {e}")

    logger.info("应用关闭中...")


app = FastAPI(
    title="LogFix AI",
    description="日志文件切分服务",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    logger.error(f"未处理的异常: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "服务器内部错误",
            },
        }
    )


# 注册路由
app.include_router(router)


@app.get("/")
async def root():
    """健康检查"""
    return {"status": "ok", "service": "LogFix AI"}


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "LogFix AI",
        "version": "0.1.0",
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
