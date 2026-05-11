import logging
from typing import AsyncIterator

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from src.agent.prompts.qa_prompts import QA_SYSTEM_PROMPT
from src.agent.state.qa_state import QAState
from src.tools.registry import TOOLS_BY_NAME
from src.utils.llm_factory import get_llm

logger = logging.getLogger(__name__)

QA_TOOLS = [
    TOOLS_BY_NAME["get_alerts"],
    TOOLS_BY_NAME["get_alert_detail"],
    TOOLS_BY_NAME["get_inverter_latest"],
    TOOLS_BY_NAME["get_inverter_trend"],
    TOOLS_BY_NAME["get_station_status"],
]

_tool_node = ToolNode(QA_TOOLS)


async def _classify_and_decide(state: QAState) -> dict:
    llm = get_llm(temperature=0.1).bind_tools(QA_TOOLS)
    prompt = (
        f"{QA_SYSTEM_PROMPT}\n\n"
        f"当前用户提问：{state['question']}\n\n"
        "请先判断意图，如果需要数据则调用对应工具；如果是 general 则直接回答。"
    )
    resp = await llm.ainvoke([HumanMessage(content=prompt)])
    return {"messages": [resp]}


def _route_after_classify(state: QAState) -> str:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return "generate"


async def _generate_answer(state: QAState) -> dict:
    llm = get_llm(temperature=0.3)
    messages = [SystemMessage(content=QA_SYSTEM_PROMPT)] + list(state["messages"])
    messages.append(HumanMessage(content=f"基于以上信息，回答用户问题：{state['question']}"))
    resp = await llm.ainvoke(messages)
    return {"answer": resp.content, "messages": [resp]}


def build_qa_graph() -> StateGraph:
    workflow = StateGraph(QAState)
    workflow.add_node("classify", _classify_and_decide)
    workflow.add_node("tools", _tool_node)
    workflow.add_node("generate", _generate_answer)
    workflow.set_entry_point("classify")
    workflow.add_conditional_edges("classify", _route_after_classify, {
        "tools": "tools",
        "generate": "generate",
    })
    workflow.add_edge("tools", "generate")
    workflow.add_edge("generate", END)
    return workflow.compile()


qa_graph = build_qa_graph()


# ── Streaming QA ──────────────────────────────────────

async def qa_stream(question: str) -> AsyncIterator[dict]:
    """流式执行 QA：先跑 classify + tools，再逐 token 流式生成回答。"""
    state = {"question": question, "messages": []}

    # Step 1: classify（非流式）
    yield {"event": "thinking", "data": "正在分析问题..."}
    result = await _classify_and_decide(state)
    state["messages"] = result["messages"]
    next_node = _route_after_classify(state)

    # Step 2: tools（如果需要）
    if next_node == "tools":
        called = _extract_tool_names(state)
        yield {"event": "tool", "data": f"正在查询数据: {', '.join(called)}"}
        result = await _tool_node.ainvoke(state)
        # ToolNode 返回 {"messages": [ToolMessage...]}，追加到现有消息后面
        state["messages"] = state["messages"] + result["messages"]

    # Step 3: 流式生成
    yield {"event": "generating", "data": ""}
    llm = get_llm(temperature=0.3, streaming=True)

    # 有 tool 消息时 SystemMessage 不能插在最前（破坏 tool_call 链），放到 HumanMessage 里
    has_tools = any(getattr(m, "type", None) == "tool" for m in state["messages"])
    if has_tools:
        messages = list(state["messages"])
        messages.append(HumanMessage(
            content=f"{QA_SYSTEM_PROMPT}\n\n基于以上信息，回答用户问题：{question}"
        ))
    else:
        messages = [SystemMessage(content=QA_SYSTEM_PROMPT)] + state["messages"]
        messages.append(HumanMessage(content=f"基于以上信息，回答用户问题：{question}"))

    full = []
    async for chunk in llm.astream(messages):
        if chunk.content:
            full.append(chunk.content)
            yield {"event": "token", "data": chunk.content}

    answer = "".join(full)
    state["answer"] = answer
    state["messages"].append(HumanMessage(content=answer))
    yield {"event": "done", "data": answer}


def _extract_tool_names(state: QAState) -> list[str]:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return [tc["name"] for tc in last.tool_calls]
    return ["unknown"]
