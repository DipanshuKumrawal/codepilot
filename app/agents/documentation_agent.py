from app.config import get_llm


DOCUMENTATION_PROMPT = """
You are a software documentation engineer.

User request:
{question}

Relevant code:
{code}

Generate clear Markdown documentation.

Include:
1. Purpose
2. Important functions/classes
3. Parameters
4. Return values
5. How the code works
6. Example usage when possible

Rules:
- Use only the supplied code.
- Do not invent behavior.
- Mention the actual file path.
"""


def generate_documentation(question, documents):

    llm = get_llm()

    if not documents:
        return "No relevant code was found."

    code = "\n\n".join(
        f"FILE: {doc['path']}\n{doc['content']}"
        for doc in documents
    )

    prompt = DOCUMENTATION_PROMPT.format(
        question=question,
        code=code
    )

    response = llm.invoke(prompt)

    return response.content