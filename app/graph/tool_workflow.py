from typing import TypedDict, List, Any

from langgraph.graph import (
    StateGraph,
    START,
    END
)

from langgraph.prebuilt import ToolNode

from app.config import get_llm
from app.tools.file_tools import (
    search_files,
    read_file
)


class ToolState(TypedDict):
    messages: List[Any]
    repo_path: str


tools = [
    search_files,
    read_file
]

llm = get_llm().bind_tools(tools)


def call_model(state):

    response = llm.invoke(
        state["messages"]
    )

    return {
        "messages": [
            response
        ]
    }


def should_continue(state):

    last_message = state["messages"][-1]

    if getattr(
        last_message,
        "tool_calls",
        None
    ):
        return "tools"

    return "end"


def build_tool_graph():

    graph = StateGraph(ToolState)

    graph.add_node(
        "agent",
        call_model
    )

    graph.add_node(
        "tools",
        ToolNode(tools)
    )

    graph.add_edge(
        START,
        "agent"
    )

    graph.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END
        }
    )

    graph.add_edge(
        "tools",
        "agent"
    )

    return graph.compile()