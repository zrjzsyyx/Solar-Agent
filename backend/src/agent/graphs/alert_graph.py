import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from src.agent.prompts.alert_prompts import ALERT_SYSTEM_PROMPT
from src.agent.state.alert_state import AlertState
from src.tools.registry import TOOLS_BY_NAME
from src.utils.llm_factory import get_llm

logger = logging.getLogger(__name__)


def _parse_alert(state: AlertState) -> dict:
    """将告警原始字段格式化为 LLM 可读的上下文。"""
    context = f"""## 异常告警

| 字段 | 值 |
|------|-----|
| 告警ID | {state["alert_id"]} |
| 电站 | {state["station_name"]} |
| 逆变器SN | {state["inverter_sn"]} |
| 组串编号 | 第{state["string_index"]}路 |
| 严重级别 | {state["severity"]} |
| 电压偏差 | {state["deviation_pct"]}%（阈值 {state.get("threshold_pct", 5)}%） |
| 检测时间 | {state.get("detected_at", "未知")} |
| 描述 | {state["description"]} |

## 逆变器快照数据 (raw_context)

```
{state.get("raw_context", "无")}
```

请分析以上异常，给出可能根因和处理建议。"""
    return {"messages": [HumanMessage(content=context)]}


async def _analyze(state: AlertState) -> dict:
    """LLM 分析节点：基于 alert 数据生成根因分析和处理建议。"""
    llm = get_llm(temperature=0.3)
    messages = [SystemMessage(content=ALERT_SYSTEM_PROMPT)] + list(state["messages"])
    resp = await llm.ainvoke(messages)

    text = resp.content
    analysis = ""
    suggestion = ""

    if "### 分析" in text and "### 处理建议" in text:
        parts = text.split("### 处理建议")
        analysis = parts[0].replace("### 分析", "").strip()
        suggestion = parts[1].strip()

    return {
        "analysis": analysis or text,
        "suggestion": suggestion or text,
        "messages": [resp],
    }


async def _build_push_args(state: AlertState) -> dict:
    """构造推送参数，供 ToolNode 调用 push_frontend_sse。"""
    return {
        "messages": [
            HumanMessage(
                content="推送告警分析到前端和飞书",
                tool_calls=[{
                    "id": "push_sse_1",
                    "name": "push_frontend_sse",
                    "args": {
                        "alert_id": state["alert_id"],
                        "suggestion": state.get("suggestion", ""),
                        "analysis": state.get("analysis", ""),
                        "station_name": state["station_name"],
                        "severity": state["severity"],
                        "deviation_pct": state["deviation_pct"],
                    },
                }]
            )
        ]
    }


async def _build_ack_args(state: AlertState) -> dict:
    """构造 ack 参数。"""
    return {
        "messages": [
            HumanMessage(
                content="确认告警",
                tool_calls=[{
                    "id": "ack_1",
                    "name": "ack_alert",
                    "args": {"alert_id": state["alert_id"]},
                }]
            )
        ]
    }


def build_alert_graph() -> StateGraph:
    workflow = StateGraph(AlertState)

    workflow.add_node("parse", _parse_alert)
    workflow.add_node("analyze", _analyze)
    workflow.add_node("push_sse", ToolNode([TOOLS_BY_NAME["push_frontend_sse"]]))
    workflow.add_node("ack", ToolNode([TOOLS_BY_NAME["ack_alert"]]))

    workflow.set_entry_point("parse")
    workflow.add_edge("parse", "analyze")
    workflow.add_edge("analyze", "push_sse")
    workflow.add_edge("push_sse", "ack")
    workflow.add_edge("ack", END)

    return workflow.compile()


alert_graph = build_alert_graph()
