from langgraph.graph import StateGraph, START, END
from agent.state import AgentState
from agent.nodes import plan_node, execute_node, refine_node

MAX_RETRIES = 2


def should_retry(state: AgentState) -> str:
    if state.get("is_sufficient"):
        return END
    if state.get("retry_count", 0) >= MAX_RETRIES:
        return END
    return "execute"


def after_plan(state: AgentState) -> str:
    if state.get("search_needed"):
        return "execute"
    return "execute_direct"


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("plan", plan_node)
    graph.add_node("execute", execute_node)
    graph.add_node("execute_direct", execute_node)
    graph.add_node("refine", refine_node)

    graph.add_edge(START, "plan")
    graph.add_conditional_edges("plan", after_plan, {
        "execute": "execute",
        "execute_direct": "execute_direct",
    })
    graph.add_edge("execute_direct", END)
    graph.add_edge("execute", "refine")
    graph.add_conditional_edges(
        "refine",
        should_retry,
        {"execute": "execute", END: END},
    )

    return graph.compile()
