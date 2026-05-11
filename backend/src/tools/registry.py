from langchain_core.tools import BaseTool

from src.tools.alert_tools import ack_alert, close_alert, get_alert_detail, get_alerts
from src.tools.inverter_tools import get_inverter_latest, get_inverter_trend
from src.tools.notification_tools import push_feishu, push_frontend_sse
from src.tools.station_tools import get_station_status

ALL_TOOLS: list[BaseTool] = [
    get_alerts,
    get_alert_detail,
    ack_alert,
    close_alert,
    get_inverter_latest,
    get_inverter_trend,
    get_station_status,
    push_frontend_sse,
    push_feishu,
]

TOOLS_BY_NAME: dict[str, BaseTool] = {t.name: t for t in ALL_TOOLS}


def get_tools(*names: str) -> list[BaseTool]:
    """按名取工具，不传则返回全部。"""
    if not names:
        return ALL_TOOLS
    return [TOOLS_BY_NAME[n] for n in names]
