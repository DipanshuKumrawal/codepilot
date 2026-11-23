from langgraph.graph import (
    StateGraph,
    START,
    END
)

from app.graph.state import CodeAgentState

from app.graph.nodes import (
    classify_question,
    code_search_node,
    debugging_node,
    testing_node,
    documentation_node,
    architecture_node,
    general_node,
    analyze_code,
    generate_final_answer,
    execute_tests_node
)


def route_question(state):

    intent = state["intent"]

    print(
        f"[Graph] Routing to: {intent}"
    )

    return intent


def route_test_result(state):

    result = state.get(
        "test_result",
        {}
    )

    return_code = result.get(
        "return_code"
    )

    attempts = state.get(
        "attempts",
        0
    )

    # Tests passed
    if return_code == 0:
        return "success"

    # Maximum attempts reached
    if attempts >= 2:
        return "failed"

    # Try again
    return "retry"


def build_graph():

    graph = StateGraph(
        CodeAgentState
    )

    # -------------------------
    # Nodes
    # -------------------------

    graph.add_node(
        "classify_question",
        classify_question
    )

    graph.add_node(
        "code_search",
        code_search_node
    )

    graph.add_node(
        "debugging",
        debugging_node
    )

    graph.add_node(
        "testing",
        testing_node
    )

    graph.add_node(
        "documentation",
        documentation_node
    )

    graph.add_node(
        "architecture",
        architecture_node
    )

    graph.add_node(
        "general",
        general_node
    )

    graph.add_node(
        "analyze_code",
        analyze_code
    )

    graph.add_node(
        "generate_final_answer",
        generate_final_answer
    )

    graph.add_node(
        "execute_tests",
        execute_tests_node
    )

    # -------------------------
    # Start
    # -------------------------

    graph.add_edge(
        START,
        "classify_question"
    )

    # -------------------------
    # Conditional routing
    # -------------------------

    graph.add_conditional_edges(
        "classify_question",
        route_question,
        {
            "code_search": "code_search",
            "debugging": "debugging",
            "testing": "testing",
            "documentation": "documentation",
            "architecture": "architecture",
            "general": "general"
        }
    )

    graph.add_edge(
        "code_search",
        "analyze_code"
    )

    graph.add_edge(
        "analyze_code",
        "generate_final_answer"
    )

    graph.add_edge(
        "debugging",
        "generate_final_answer"
    )

    graph.add_edge(
        "documentation",
        "generate_final_answer"
    )

    graph.add_edge(
        "architecture",
        "generate_final_answer"
    )

    graph.add_edge(
        "general",
        "generate_final_answer"
    )
    graph.add_edge(
        "testing",
        "execute_tests"
    )

    graph.add_conditional_edges(
        "execute_tests",
        route_test_result,
        {
            "success": "generate_final_answer",
            "retry": "testing",
            "failed": "generate_final_answer"
        }
    )

    # -------------------------
    # End
    # -------------------------

    graph.add_edge(
        "generate_final_answer",
        END
    )

    return graph.compile()