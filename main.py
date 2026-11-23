from app.graph.workflow import build_graph


graph = build_graph()


questions = [

    "Where is authentication implemented?",

    "Why am I getting a KeyError?",

    "Create unit tests for this function.",

    "Explain the architecture of this project."
]


for question in questions:

    print("\n" + "=" * 60)

    print(
        f"QUESTION: {question}"
    )

    result = graph.invoke(
        {
            "question": question,

            "repo_path":
                "./sample_project",

            "intent": "",

            "retrieved_documents": [],

            "analysis": "",

            "final_answer": "",

            "messages": [],

            "attempts": 0
        }
    )

    print(
        f"\nINTENT: "
        f"{result['intent']}"
    )

    print(
        "\nANSWER:\n"
        f"{result['final_answer']}"
    )