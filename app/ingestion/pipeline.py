import os
import shutil

from app.ingestion.loader import load_repository
from app.ingestion.chunker import chunk_documents

from app.ingestion.vectorstore import (
    create_vectorstore,
    save_vectorstore,
    vectorstore_exists,
    get_vectorstore_path
)


def delete_index(repo_path: str):
    """Remove the stored vector index of a repository."""

    path = get_vectorstore_path(repo_path)

    if os.path.isdir(path):
        shutil.rmtree(path)
        return True

    return False


def index_repository(repo_path: str, force: bool = False):

    print(
        f"[Indexer] Indexing repository: {repo_path}"
    )

    if force:
        delete_index(repo_path)

    if vectorstore_exists(repo_path):

        print(
            "[Indexer] Vector store already exists."
        )

        return {
            "files": 0,
            "chunks": 0,
            "vectorstore": "already_exists"
        }

    documents = load_repository(repo_path)

    if not documents:

        raise ValueError(
            "No supported source files found."
        )

    print(
        f"[Indexer] Loaded {len(documents)} files"
    )

    chunks = chunk_documents(
        documents
    )

    print(
        f"[Indexer] Created {len(chunks)} chunks"
    )

    vectorstore = create_vectorstore(
        chunks
    )

    vectorstore_path = save_vectorstore(
        vectorstore,
        repo_path
    )

    print(
        "[Indexer] Vector store created."
    )

    return {
        "files": len(documents),
        "chunks": len(chunks),
        "vectorstore": vectorstore_path
    }