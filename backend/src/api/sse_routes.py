import asyncio
import json
import logging

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from starlette.requests import Request

from src.utils.sse_manager import sse_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sse", tags=["sse"])


@router.get("/agent-alerts")
async def sse_alert_stream(request: Request):
    """前端订阅此 SSE 端点，接收 Agent 处理后的告警（含 LLM 分析建议）。"""

    async def event_generator():
        cid, queue = sse_manager.connect()
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {data}\n\n"
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"
        finally:
            sse_manager.disconnect(cid)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
