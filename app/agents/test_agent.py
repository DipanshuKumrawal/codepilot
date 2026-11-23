from app.config import get_llm


TEST_PROMPT = """
You are an expert Python test engineer.

The user wants tests for code in an existing repository.

User request:
{question}

Relevant repository code:

{code}

Generate pytest unit tests for the relevant code.

Requirements:

1. Identify the function/class that should be tested.
2. Test normal behavior.
3. Test edge cases.
4. Test invalid input where appropriate.
5. Use pytest.
6. Use mocks when an external dependency needs to be isolated.
7. Do not invent external dependencies.
8. Do not assume behavior that is not present in the code.
9. Keep the tests focused on the supplied code.
10. Include useful test names.

Return ONLY valid Python test code.
"""


def generate_tests(question, documents):

    llm = get_llm()

    if not documents:
        return (
            "No relevant code was retrieved, "
            "so tests cannot be generated reliably."
        )

    code_parts = []

    for document in documents:

        code_parts.append(
            f"""
FILE: {document['path']}

LANGUAGE: {document.get('language', 'text')}

CODE:

{document['content']}
"""
        )

    code = "\n\n".join(code_parts)

    prompt = TEST_PROMPT.format(
        question=question,
        code=code
    )

    response = llm.invoke(prompt)

    return response.content