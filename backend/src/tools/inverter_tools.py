from langchain_core.tools import tool

from src.services.data_backend_client import backend


@tool
async def get_inverter_latest(sn: str) -> dict:
    """查询某台逆变器的最新实时读数（电压、电流、功率等）。参数 sn 为逆变器序列号。"""
    resp = await backend.get_inverter_latest(sn)
    return {
        "time": resp.data.time,
        "state": resp.data.state,
        "pac": resp.data.pac,
        "power": resp.data.power,
        "dc_input_type": resp.data.dc_input_type,
        "payload": resp.data.payload,
    }


@tool
async def get_inverter_trend(sn: str, string_index: int, days: int = 1) -> dict:
    """查询某台逆变器某路直流接口的历史电压趋势。参数 sn 为序列号，string_index 为接口编号(1~32)，days 为查询天数。"""
    from datetime import datetime, timedelta, timezone

    end = datetime.now(timezone.utc).isoformat()
    start = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    resp = await backend.get_inverter_trend(sn, string_index, start=start, end=end)
    points = []
    for p in resp.data:
        points.append({
            "time": p.time,
            "voltage": p.voltage,
            "reference_voltage": p.reference_voltage,
            "deviation_pct": p.deviation_pct,
        })
    return {"sn": sn, "string_index": string_index, "points": points}
