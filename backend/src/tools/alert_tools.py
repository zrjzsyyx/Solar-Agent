from langchain_core.tools import tool

from src.services.data_backend_client import backend


@tool
async def get_alerts(status: str = "OPEN", limit: int = 10, station_id: int = 0) -> dict:
    """查询告警列表。参数 status 可选 OPEN/ACKED/CLOSED，limit 默认 10，station_id 可选（0 表示不过滤）。返回告警列表。"""
    sid = station_id if station_id > 0 else None
    resp = await backend.list_alerts(status=status, limit=limit, station_id=sid)
    items = []
    for a in resp.data.items:
        items.append({
            "id": a.id,
            "station_name": a.station_name,
            "inverter_sn": a.inverter_sn,
            "string_index": a.string_index,
            "severity": a.severity,
            "deviation_pct": a.deviation_pct,
            "description": a.description,
            "detected_at": str(a.detected_at) if a.detected_at else None,
        })
    return {"total": resp.data.total, "items": items}


@tool
async def get_alert_detail(alert_id: int) -> dict:
    """查询单条告警的完整详情，包含 raw_context（告警瞬间的逆变器完整数据）。"""
    resp = await backend.get_alert(alert_id)
    a = resp.data
    return {
        "id": a.id,
        "station_name": a.station_name,
        "inverter_sn": a.inverter_sn,
        "string_index": a.string_index,
        "severity": a.severity,
        "status": a.status,
        "voltage": a.voltage,
        "reference_voltage": a.reference_voltage,
        "deviation_pct": a.deviation_pct,
        "threshold_pct": a.threshold_pct,
        "detected_at": str(a.detected_at) if a.detected_at else None,
        "description": a.description,
        "raw_context": a.raw_context,
    }


@tool
async def ack_alert(alert_id: int) -> str:
    """确认告警，Agent 处理完成的告警应调用此工具确认，防止重复处理。"""
    await backend.ack_alert(alert_id)
    return f"告警 {alert_id} 已确认"


@tool
async def close_alert(alert_id: int, note: str = "") -> str:
    """关闭告警并附带处理备注。参数 note 为人工填写的处理说明。"""
    await backend.close_alert(alert_id, note)
    return f"告警 {alert_id} 已关闭"
