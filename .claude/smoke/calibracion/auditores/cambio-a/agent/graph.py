"""Grafo del bot de pedidos."""
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from .tools import get_order_status, list_recent_orders

TOOLS = [list_recent_orders, get_order_status]

# workaround: #233 — langgraph no propaga las etiquetas a los subgrafos; se repiten aquí a mano
RUN_CONFIG = {"tags": ["shop-bot"], "run_name": "shop-bot"}


def call_model(state: MessagesState) -> dict:
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0).bind_tools(TOOLS)
    return {"messages": [model.invoke(state["messages"], config=RUN_CONFIG)]}


def build_graph():
    graph = StateGraph(MessagesState)
    graph.add_node("model", call_model)
    graph.add_node("tools", ToolNode(TOOLS))
    graph.add_edge(START, "model")
    graph.add_conditional_edges("model", tools_condition)
    graph.add_edge("tools", "model")
    return graph.compile().with_config(RUN_CONFIG)
