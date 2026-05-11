from typing import Annotated, Literal, NotRequired, TypedDict

from langgraph.graph.message import add_messages


class ReportState(TypedDict):
    report_type: Literal["weekly", "monthly"]
    period_start: NotRequired[str]
    period_end: NotRequired[str]
    report_markdown: NotRequired[str]
    error: NotRequired[str]

    messages: Annotated[list, add_messages]
