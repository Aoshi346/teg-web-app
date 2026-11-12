"""Grafo del bot de pedidos."""
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from .model import get_model
from .tools import get_order_status, list_recent_orders

TOOLS = [list_recent_orders, get_order_status]


def call_model(state: MessagesState) -> dict:
    model = get_model().bind_tools(TOOLS)
    return {"messages": [model.invoke(state["messages"])]}


def build_graph():
    graph = StateGraph(MessagesState)
    graph.add_node("model", call_model)
    graph.add_node("tools", ToolNode(TOOLS))
    graph.add_edge(START, "model")
    graph.add_conditional_edges("model", tools_condition)
    graph.add_edge("tools", "model")
    return graph.compile()
