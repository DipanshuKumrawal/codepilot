import os

from dotenv import load_dotenv

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
import hashlib


load_dotenv()


BASE_VECTORSTORE_PATH = os.path.join(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )
    ),
    "data",
    "vectorstores"
)


def get_embeddings():

    return HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')


def get_repository_id(repo_path: str):
    """
    Create a stable ID for each repository path.
    """

    absolute_path = os.path.abspath(repo_path)

    repo_id = hashlib.md5(
        absolute_path.encode("utf-8")
    ).hexdigest()[:12]

    return repo_id


def get_vectorstore_path(repo_path: str):
    """
    Return the vector store directory
    for a specific repository.
    """

    repo_id = get_repository_id(repo_path)

    return os.path.join(
        BASE_VECTORSTORE_PATH,
        repo_id
    )


def create_vectorstore(chunks):

    documents = []

    for chunk in chunks:

        documents.append(
            Document(
                page_content=chunk["content"],
                metadata={
                    "path": chunk["path"],
                    "extension": chunk["extension"],
                    "language": chunk.get(
                        "language",
                        "text"
                    ),
                    "chunk_id": chunk["chunk_id"]
                }
            )
        )

    embeddings = get_embeddings()

    vectorstore = FAISS.from_documents(
        documents,
        embeddings
    )

    return vectorstore


def save_vectorstore(
    vectorstore,
    repo_path: str
):

    path = get_vectorstore_path(repo_path)

    os.makedirs(
        path,
        exist_ok=True
    )

    vectorstore.save_local(path)

    return path


def load_vectorstore(
    repo_path: str
):

    embeddings = get_embeddings()

    path = get_vectorstore_path(repo_path)

    return FAISS.load_local(
        path,
        embeddings,
        allow_dangerous_deserialization=True
    )


def vectorstore_exists(
    repo_path: str
):

    path = get_vectorstore_path(repo_path)

    return (
        os.path.exists(path)
        and os.path.exists(
            os.path.join(
                path,
                "index.faiss"
            )
        )
        and os.path.exists(
            os.path.join(
                path,
                "index.pkl"
            )
        )
    )