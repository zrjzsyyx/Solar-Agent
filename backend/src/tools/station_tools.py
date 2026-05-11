from langchain_core.tools import tool

from src.services.data_backend_client import backend


@tool
async def get_station_status(station_id: int) -> dict:
    """查询某个电站的整体状态，包括在线设备数量、未关闭告警数、最新告警列表。station_id 为 19 位长整型数字。"""
    resp = await backend.get_station_status(station_id)
    s = resp.data
    alerts = []
    for a in s.latest_alerts:
        alerts.append({
            "id": a.id,
            "inverter_sn": a.inverter_sn,
            "severity": a.severity,
            "deviation_pct": a.deviation_pct,
            "description": a.description,
        })
    return {
        "station_id": s.station_id,
        "online_device_count": s.online_device_count,
        "open_alert_count": s.open_alert_count,
        "latest_alerts": alerts,
    }
