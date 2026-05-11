from typing import Annotated, NotRequired, TypedDict

from langgraph.graph.message import add_messages


class QAState(TypedDict):
    question: str
    intent: NotRequired[str]
    answer: NotRequired[str]
    error: NotRequired[str]

    messages: Annotated[list, add_messages]
