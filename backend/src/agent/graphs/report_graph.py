import logging
from datetime import datetime, timezone

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from src.agent.prompts.report_prompts import REPORT_SYSTEM_PROMPT
from src.agent.state.report_state import ReportState
from src.services.data_backend_client import backend
from src.tools.registry import TOOLS_BY_NAME
from src.utils.llm_factory import get_llm

logger = logging.getLogger(__name__)


async def _gather_data(state: ReportState) -> dict:
    """收集数据：获取所有告警并汇总。"""
    period_label = "周" if state["report_type"] == "weekly" else "月"

    alerts = await backend.list_alerts(
        start=state.get("period_start"),
        end=state.get("period_end"),
        limit=500,
    )

    summary_parts = [f"## 数据汇总\n"]
    summary_parts.append(f"周期内共 **{alerts.data.total}** 条告警")

    severity_counts = {"WARNING": 0, "CRITICAL": 0}
    stations = {}
    top_alerts = []

    for a in alerts.data.items:
        severity_counts[a.severity] = severity_counts.get(a.severity, 0) + 1
        stations[a.station_name] = stations.get(a.station_name, 0) + 1
        if len(top_alerts) < 5:
            top_alerts.append(
                f"- {a.station_name} | {a.inverter_sn} 第{a.string_index}路 | "
                f"{a.severity} | 偏差 {a.deviation_pct}% | {a.detected_at}"
            )

    summary_parts.append(f"WARNING: {severity_counts['WARNING']}，CRITICAL: {severity_counts['CRITICAL']}")
    summary_parts.append("\n### 各电站告警分布")
    for name, count in stations.items():
        summary_parts.append(f"- {name}: {count} 条")
    summary_parts.append("\n### 严重告警 TOP 5")
    summary_parts.extend(top_alerts)

    return {
        "messages": [HumanMessage(content="\n".join(summary_parts))],
    }


async def _generate_report(state: ReportState) -> dict:
    """LLM 节点：基于汇总数据生成报告。"""
    llm = get_llm(temperature=0.3)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    period_label = "周" if state["report_type"] == "weekly" else "月"

    prompt = REPORT_SYSTEM_PROMPT.format(
        电站名称="全部",
        周期=period_label,
        起始日期=state.get("period_start", "最近"),
        结束日期=state.get("period_end", "至今"),
        当前时间=now,
    )

    messages = [SystemMessage(content=prompt)] + list(state["messages"])
    resp = await llm.ainvoke(messages)

    return {
        "report_markdown": resp.content,
        "messages": [resp],
    }


async def _build_push_args(state: ReportState) -> dict:
    """构造报告推送参数。"""
    return {
        "messages": [
            HumanMessage(
                content="推送报告到前端",
                tool_calls=[{
                    "id": "push_sse_r",
                    "name": "push_frontend_sse",
                    "args": {
                        "alert_id": 0,
                        "suggestion": state.get("report_markdown", ""),
                        "analysis": f"{state['report_type']} 报告",
                        "station_name": "全部电站",
                        "severity": "INFO",
                        "deviation_pct": 0,
                    },
                }]
            )
        ]
    }


def build_report_graph() -> StateGraph:
    workflow = StateGraph(ReportState)

    workflow.add_node("gather", _gather_data)
    workflow.add_node("generate", _generate_report)
    workflow.add_node("push", ToolNode([TOOLS_BY_NAME["push_frontend_sse"]]))

    workflow.set_entry_point("gather")
    workflow.add_edge("gather", "generate")
    workflow.add_edge("generate", "push")
    workflow.add_edge("push", END)

    return workflow.compile()


report_graph = build_report_graph()
