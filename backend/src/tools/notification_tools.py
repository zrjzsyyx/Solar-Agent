import json
import logging

from langchain_core.tools import tool

from src.utils.sse_manager import sse_manager

logger = logging.getLogger(__name__)


@tool
async def push_frontend_sse(alert_id: int, suggestion: str, analysis: str, **kwargs) -> str:
    """将处理过的告警（含 LLM 分析结果和建议）通过 SSE 推送到前端。"""
    await sse_manager.broadcast_alert({
        "alert_id": alert_id,
        "suggestion": suggestion,
        "analysis": analysis,
        "station_name": kwargs.get("station_name", ""),
        "severity": kwargs.get("severity", ""),
        "deviation_pct": kwargs.get("deviation_pct", 0),
    })
    return f"SSE 推送完成，当前 {sse_manager.client_count} 个客户端"


@tool
async def push_feishu(title: str, content: str) -> str:
    """飞书推送占位。后续接入飞书 Webhook 后启用。"""
    logger.info(f"[飞书占位] {title}\n{content[:300]}")
    return "飞书推送占位完成"
