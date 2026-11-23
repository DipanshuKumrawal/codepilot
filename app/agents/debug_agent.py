from app.config import get_llm
import re

def extract_code_change(response):

    file_match = re.search(
        r"FILE:\s*(.+)",
        response,
        re.IGNORECASE
    )

    code_match = re.search(
        r"FIXED CODE:\s*```(?:python)?\s*(.*?)```",
        response,
        re.IGNORECASE | re.DOTALL
    )

    if not file_match or not code_match:
        return None

    return {
        "file": file_match.group(1).strip(),
        "new_content": code_match.group(1).strip()
    }


DEBUG_PROMPT = """
You are an expert software debugging engineer.

The user is debugging a software project.

User question:
{question}

Relevant repository code:

{code}

Analyze the problem carefully.

Provide:

1. Root Cause
   - Identify the most likely cause of the problem.

2. Relevant File
   - Mention the file path where the problem appears.

3. Relevant Function/Class
   - Mention the relevant function, class, or code block.

4. Why It Happens
   - Explain the execution flow that leads to the error.

5. Suggested Fix
   - Explain the concrete change that should be made.

6. Example Fix
   - Provide corrected code when the retrieved code is
     sufficient.

7. Potential Side Effects
   - Mention anything else that could be affected.

Rules:

- Use ONLY the supplied repository code.
- Do not invent files.
- Do not invent functions.
- Do not assume dependencies that are not shown.
- If the retrieved code is insufficient, clearly say so.

If (and only if) you can fix a single file, finish your answer with
exactly this block so the fix can be reviewed in the UI:

FILE: <path relative to the repository root>
FIXED CODE:
```
<the complete new content of that file>
```
"""


def analyze_debugging_problem(
    question,
    documents
):

    llm = get_llm()

    if not documents:

        return (
            "I could not retrieve relevant code "
            "from the repository, so I cannot "
            "reliably diagnose the problem."
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

    prompt = DEBUG_PROMPT.format(
        question=question,
        code=code
    )

    response = llm.invoke(prompt)

    return response.content