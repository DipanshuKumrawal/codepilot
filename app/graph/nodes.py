from app.config import get_llm
import os

from app.prompts.prompts import (
    ROUTER_PROMPT,
    ANALYSIS_PROMPT,
    FINAL_PROMPT
)

from app.ingestion.vectorstore import (
    load_vectorstore,
    vectorstore_exists
)

from app.agents.debug_agent import (
    analyze_debugging_problem
)

from app.agents.test_agent import generate_tests

from app.agents.architecture_agent import (
    generate_architecture_summary
)

from app.ingestion.loader import (
    load_repository
)

from app.agents.documentation_agent import (
    generate_documentation
)

from app.tools.test_tools import run_test_file
from app.agents.test_agent import generate_tests


VECTORSTORE_PATH = "./data/vectorstore"


# --------------------------------------------------
# Router
# --------------------------------------------------

def classify_question(state):

    llm = get_llm()

    prompt = ROUTER_PROMPT.format(
        question=state["question"]
    )

    response = llm.invoke(prompt)

    intent = (
        response.content
        .strip()
        .lower()
    )

    valid_intents = {
        "code_search",
        "debugging",
        "testing",
        "documentation",
        "architecture",
        "general"
    }

    if intent not in valid_intents:

        intent = "code_search"

    print(
        f"[Router] Intent: {intent}"
    )

    return {
        "intent": intent
    }


# --------------------------------------------------
# Retrieve code
# --------------------------------------------------

def retrieve_code(state):

    repo_path = state["repo_path"]

    if not vectorstore_exists(repo_path):

        return {
            "retrieved_documents": [],
            "analysis": (
                "No vector database was found. "
                "Please index the repository first."
            )
        }

    vectorstore = load_vectorstore(
        repo_path
    )

    results = vectorstore.similarity_search(
        state["question"],
        k=5
    )

    retrieved_documents = []

    for result in results:

        retrieved_documents.append(
            {
                "content": result.page_content,
                "path": result.metadata.get("path"),
                "extension": result.metadata.get(
                    "extension"
                ),
                "language": result.metadata.get(
                    "language"
                ),
                "chunk_id": result.metadata.get(
                    "chunk_id"
                )
            }
        )

    print(
        f"[Retriever] Retrieved "
        f"{len(retrieved_documents)} documents"
    )

    return {
        "retrieved_documents":
            retrieved_documents
    }

# --------------------------------------------------
# Analyze code
# --------------------------------------------------

def analyze_code(state):

    llm = get_llm()

    code = "\n\n".join(
        [
            (
                f"FILE: {doc['path']}\n"
                f"{doc['content']}"
            )
            for doc in
            state["retrieved_documents"]
        ]
    )

    history = "\n".join(
        [
            f"{message['role']}: "
            f"{message['content']}"
            for message in
            state.get("messages", [])
        ]
    )

    prompt = ANALYSIS_PROMPT.format(
        question=state["question"],
        code=code,
        history=history
    )

    response = llm.invoke(prompt)

    return {
        "analysis": response.content
    }


# --------------------------------------------------
# Final answer
# --------------------------------------------------

def generate_final_answer(state):

    llm = get_llm()

    files = "\n".join(
        sorted(
            {
                doc["path"]
                for doc in state.get(
                    "retrieved_documents",
                    []
                )
            }
        )
    )

    history = "\n".join(
        [
            f"{message['role']}: {message['content']}"
            for message in state.get(
                "messages",
                []
            )
        ]
    )

    prompt = FINAL_PROMPT.format(
        question=state["question"],
        analysis=state["analysis"],
        files=files,
        history=history,
        intent=state["intent"]
    )

    response = llm.invoke(prompt)

    return {
        "final_answer": response.content
    }


def code_search_node(state):

    print("[Agent] Running Code Search Agent")

    repo_path = state["repo_path"]

    if not vectorstore_exists(repo_path):
        return {
            "retrieved_documents": [],
            "analysis": (
                "No vector store exists for this repository. "
                "Please index the repository first."
            )
        }

    vectorstore = load_vectorstore(repo_path)

    results = vectorstore.similarity_search_with_score(
        state["question"],
        k=8
    )

    retrieved_documents = []

    for document, score in results:

        retrieved_documents.append(
            {
                "content": document.page_content,
                "path": document.metadata.get("path"),
                "extension": document.metadata.get(
                    "extension"
                ),
                "language": document.metadata.get(
                    "language"
                ),
                "chunk_id": document.metadata.get(
                    "chunk_id"
                ),
                "score": float(score)
            }
        )

    print(
        f"[Code Search] Retrieved "
        f"{len(retrieved_documents)} chunks"
    )

    return {
        "retrieved_documents": retrieved_documents
    }

def debugging_node(state):

    print("[Agent] Running Debugging Agent")

    repo_path = state["repo_path"]

    if not vectorstore_exists(repo_path):

        return {
            "retrieved_documents": [],
            "analysis": (
                "No vector store exists for this repository."
            ),
            "pending_change": {}
        }

    vectorstore = load_vectorstore(repo_path)

    results = vectorstore.similarity_search(
        state["question"],
        k=8
    )

    retrieved_documents = []

    for document in results:

        retrieved_documents.append(
            {
                "content": document.page_content,
                "path": document.metadata.get("path"),
                "extension": document.metadata.get("extension"),
                "language": document.metadata.get("language"),
                "chunk_id": document.metadata.get("chunk_id")
            }
        )

    print(
        f"[Debugging] Retrieved "
        f"{len(retrieved_documents)} chunks"
    )

    analysis = analyze_debugging_problem(
        state["question"],
        retrieved_documents
    )

    from app.agents.debug_agent import (
        extract_code_change
    )

    change = extract_code_change(
        analysis
    )

    return {
        "retrieved_documents": retrieved_documents,
        "analysis": analysis,
        "pending_change": change or {}
    }

def testing_node(state):

    print("[Agent] Running Testing Agent")

    repo_path = state["repo_path"]

    attempts = state.get(
        "attempts",
        0
    ) + 1

    print(
        f"[Testing] Attempt {attempts}"
    )

    if not vectorstore_exists(repo_path):

        return {
            "retrieved_documents": [],
            "analysis": (
                "No vector store exists for this repository."
            )
        }

    vectorstore = load_vectorstore(repo_path)

    results = vectorstore.similarity_search(
        state["question"],
        k=8
    )

    retrieved_documents = []

    for document in results:

        retrieved_documents.append(
            {
                "content": document.page_content,
                "path": document.metadata.get(
                    "path"
                ),
                "extension": document.metadata.get(
                    "extension"
                ),
                "language": document.metadata.get(
                    "language"
                ),
                "chunk_id": document.metadata.get(
                    "chunk_id"
                )
            }
        )

    print(
        f"[Testing] Retrieved "
        f"{len(retrieved_documents)} chunks"
    )

    generated_tests = generate_tests(
        state["question"],
        retrieved_documents
    )

    return {
        "retrieved_documents": retrieved_documents,
        "analysis": generated_tests,
        "test_code": generated_tests,
        "attempts": attempts
    }


def documentation_node(state):

    print("[Agent] Running Documentation Agent")

    repo_path = state["repo_path"]

    vectorstore = load_vectorstore(repo_path)

    results = vectorstore.similarity_search(
        state["question"],
        k=8
    )

    documents = []

    for document in results:
        documents.append({
            "content": document.page_content,
            "path": document.metadata.get("path"),
            "extension": document.metadata.get("extension"),
            "language": document.metadata.get("language"),
            "chunk_id": document.metadata.get("chunk_id")
        })

    print(
        f"[Documentation] Retrieved "
        f"{len(documents)} chunks"
    )

    analysis = generate_documentation(
        state["question"],
        documents
    )

    return {
        "retrieved_documents": documents,
        "analysis": analysis
    }

def architecture_node(state):

    print("[Agent] Running Architecture Agent")

    repo_path = state["repo_path"]

    if not repo_path:

        return {
            "analysis": (
                "Repository path is not available."
            ),
            "retrieved_documents": []
        }

    files = load_repository(
        repo_path
    )

    print(
        f"[Architecture] Loaded "
        f"{len(files)} files"
    )

    analysis = generate_architecture_summary(
        state["question"],
        files
    )

    return {
        "retrieved_documents": files,
        "analysis": analysis
    }


def general_node(state):

    print("[Agent] Running General Agent")

    return {
        "analysis": (
            "This question is not directly related "
            "to repository code."
        )
    }


def execute_tests_node(state):

    print("[Agent] Running pytest")

    repo_path = state["repo_path"]

    test_file = "generated_test.py"

    test_path = os.path.join(
        repo_path,
        test_file
    )

    test_code = state["test_code"]

    # Remove Markdown code fences if the LLM returned them
    if test_code.startswith("```python"):
        test_code = test_code.replace(
            "```python",
            "",
            1
        )

    if test_code.endswith("```"):
        test_code = test_code[:-3]

    test_code = test_code.strip()

    with open(
        test_path,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(test_code)

    result = run_test_file(
        repo_path,
        test_file
    )

    print(
        f"[Pytest] Return code: "
        f"{result['return_code']}"
    )

    return {
        "test_result": result
    }