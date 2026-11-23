from pathlib import Path
from langchain_core.tools import tool

from app.ingestion.loader import is_ignored


def list_repository_files(repo_path: str):
    """Return sorted relative paths of non-ignored files."""

    repo = Path(repo_path)

    return sorted(
        str(p.relative_to(repo))
        for p in repo.rglob("*")
        if p.is_file() and not is_ignored(p, repo)
    )


def search_text(repo_path: str, query: str, limit: int = 50):
    """Case-insensitive text search; returns (file, line_no, line)."""

    repo = Path(repo_path)
    q = query.lower()
    hits = []

    for rel in list_repository_files(repo_path):

        try:
            text = (repo / rel).read_text(
                encoding="utf-8",
                errors="strict"
            )
        except Exception:
            continue

        for no, line in enumerate(text.splitlines(), 1):
            if q in line.lower():
                hits.append((rel, no, line.strip()[:200]))
                if len(hits) >= limit:
                    return hits

    return hits


@tool
def search_files(repo_path: str, query: str):
    """Search for a text string inside repository files."""

    return sorted({h[0] for h in search_text(repo_path, query, 500)})


@tool
def read_file(repo_path: str, file_path: str):
    """Read a file from the selected repository."""

    repo = Path(repo_path).resolve()
    full_path = (repo / file_path).resolve()

    if repo not in full_path.parents:
        return "Path is outside the repository."

    if not full_path.is_file():
        return "File does not exist."

    return full_path.read_text(
        encoding="utf-8",
        errors="ignore"
    )
