from app.ingestion.loader import load_repository
from app.ingestion.chunker import chunk_documents
from app.ingestion.vectorstore import (
    create_vectorstore,
    save_vectorstore
)


REPOSITORY_PATH = "./sample_project"

VECTORSTORE_PATH = "./data/vectorstore"


print("Loading repository...")

documents = load_repository(REPOSITORY_PATH)

print(f"Loaded {len(documents)} files")


print("Chunking code...")

chunks = chunk_documents(documents)

print(f"Created {len(chunks)} chunks")


print("Creating vector store...")

vectorstore = create_vectorstore(chunks)

save_vectorstore(
    vectorstore,
    VECTORSTORE_PATH
)

print("Vector store created successfully.")