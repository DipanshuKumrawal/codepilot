from app.config import get_llm


ARCHITECTURE_PROMPT = """
You are a senior software architect analyzing an existing
software repository.

User request:
{question}

Repository files:

{files}

Analyze the repository and provide an architecture overview.

Include:

1. Project Purpose
   - What does this project appear to do?

2. Entry Points
   - Identify application entry points such as main.py,
     app.py, manage.py, API entry points, etc.

3. Main Components
   - Identify important modules, packages, services,
     agents, utilities, or frontend components.

4. Component Relationships
   - Explain how the major components interact.

5. Data Flow
   - Explain how data moves through the application.

6. APIs
   - Identify API endpoints or API-related components
     if present.

7. Database / Storage
   - Identify databases, files, caches, vector stores,
     or other storage mechanisms if present.

8. External Dependencies
   - Identify important external libraries or services.

9. Authentication
   - Explain authentication only if it is visible
     in the supplied code.

10. Testing
   - Identify the testing structure if present.

11. Potential Architecture Diagram
   - Provide a simple text representation of the
     architecture.

Rules:

- Use ONLY evidence from the supplied repository files.
- Do not invent components.
- Do not assume technologies that are not visible.
- Clearly say when information is unavailable.
- Mention actual file paths.
- Keep the explanation technically precise.
"""


def generate_architecture_summary(
    question,
    files
):

    llm = get_llm()

    if not files:

        return (
            "No repository files were found, "
            "so an architecture analysis cannot "
            "be generated."
        )

    file_parts = []

    for file in files:

        file_parts.append(
            f"""
FILE: {file['path']}

LANGUAGE: {file.get('extension', 'unknown')}

CONTENT:

{file['content'][:8000]}
"""
        )

    repository_text = "\n\n".join(
        file_parts
    )

    prompt = ARCHITECTURE_PROMPT.format(
        question=question,
        files=repository_text
    )

    response = llm.invoke(prompt)

    return response.content