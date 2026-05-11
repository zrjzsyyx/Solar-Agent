from typing import Annotated, NotRequired, TypedDict

from langgraph.graph.message import add_messages


class AlertState(TypedDict):
    alert_id: int
    station_name: str
    inverter_sn: str
    string_index: int
    severity: str
    deviation_pct: float
    description: str
    raw_context: str

    analysis: NotRequired[str]
    suggestion: NotRequired[str]

    messages: Annotated[list, add_messages]
