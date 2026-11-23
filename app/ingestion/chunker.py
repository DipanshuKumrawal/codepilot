from pathlib import Path

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)


LANGUAGE_MAP = {

    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".cpp": "cpp",
    ".c": "c",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".php": "php",
    ".md": "markdown",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".html": "html",
    ".css": "css",
    ".h": "c",
    ".hpp": "cpp",
    ".scss": "scss",
    ".sh": "bash",
    ".sql": "sql",
    ".toml": "toml",
    ".cs": "csharp",
    ".kt": "kotlin",
    ".swift": "swift",
    ".vue": "vue",
    ".svelte": "svelte"
}


def chunk_documents(documents):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=200
    )


    chunks = []


    for document in documents:

        extension = (
            document["extension"]
        )


        language = LANGUAGE_MAP.get(
            extension,
            "text"
        )


        split_texts = splitter.split_text(
            document["content"]
        )


        for index, text in enumerate(
            split_texts
        ):

            chunks.append({

                "content": text,

                "path": document["path"],

                "extension": extension,

                "language": language,

                "chunk_id": index

            })


    return chunks