import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.agent.graphs.qa_graph import qa_graph, qa_stream
from src.agent.graphs.report_graph import report_graph

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/agent", tags=["agent"])


class QARequest(BaseModel):
    question: str


@router.post("/qa")
async def agent_qa(req: QARequest):
    """Agent 问答接口（同步版本，保留兼容）。"""
    state = {"question": req.question, "messages": []}
    try:
        result = await qa_graph.ainvoke(state)
        return {
            "question": req.question,
            "answer": result.get("answer", "未能生成回答"),
        }
    except Exception as e:
        return {
            "question": req.question,
            "answer": f"处理出错: {str(e)}",
        }


@router.get("/qa/stream")
async def agent_qa_stream(request: Request, q: str = Query(..., description="用户问题")):
    """Agent 问答 SSE 流式接口 — 思考中提示 + 逐字推送 + Markdown 回答。"""

    async def event_generator():
        try:
            async for msg in qa_stream(q):
                event = msg["event"]
                data = msg["data"]
                sse_data = json.dumps(data, ensure_ascii=False)
                yield f"event: {event}\ndata: {sse_data}\n\n"
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"event: error\ndata: {json.dumps(str(e), ensure_ascii=False)}\n\n"

        # 保持连接短暂存活，确保 done 事件送达
        await asyncio.sleep(0.1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


class ReportGenerateRequest(BaseModel):
    report_type: str = "weekly"


@router.post("/report/generate")
async def agent_report(req: ReportGenerateRequest):
    """Agent 报表接口：生成周报或月报。"""
    now = datetime.now(timezone.utc)
    report_id = f"{req.report_type}-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}"

    state = {
        "report_type": req.report_type,
        "period_start": None,
        "period_end": None,
        "messages": [],
    }
    try:
        result = await report_graph.ainvoke(state)
        return {
            "report_id": report_id,
            "report_markdown": result.get("report_markdown", ""),
        }
    except Exception as e:
        return {
            "report_id": report_id,
            "report_markdown": f"生成失败: {str(e)}",
        }
