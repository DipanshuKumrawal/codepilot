from pathlib import Path


SUPPORTED_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".java",
    ".cpp",
    ".c",
    ".h",
    ".hpp",
    ".go",
    ".rs",
    ".php",
    ".rb",
    ".md",
    ".json",
    ".yaml",
    ".yml",
    ".html",
    ".css",
    ".scss",
    ".sh",
    ".sql",
    ".toml",
    ".txt",
    ".cs",
    ".kt",
    ".swift",
    ".vue",
    ".svelte",
}

MAX_FILE_SIZE = 500_000  # bytes; skip huge/generated files


IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".idea",
    ".vscode",
    "dist",
    "build",
    ".mypy_cache",
    ".pytest_cache",
    ".tox",
    "env",
    "site-packages",
}


def is_ignored(file_path: Path, repo: Path) -> bool:
    """True if any directory *inside* the repo is ignored."""

    try:
        parts = file_path.relative_to(repo).parts
    except ValueError:
        parts = file_path.parts

    return any(part in IGNORED_DIRECTORIES for part in parts[:-1])


def load_repository(repo_path: str):

    repo = Path(repo_path)

    if not repo.exists():
        raise ValueError(f"Repository does not exist: {repo_path}")

    documents = []

    for file_path in repo.rglob("*"):

        if not file_path.is_file():
            continue

        if is_ignored(file_path, repo):
            continue

        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        try:
            if file_path.stat().st_size > MAX_FILE_SIZE:
                continue

            content = file_path.read_text(
                encoding="utf-8",
                errors="ignore"
            )

            if not content.strip():
                continue

            documents.append({
                "path": str(file_path),
                "content": content,
                "extension": file_path.suffix.lower()
            })

        except Exception as e:
            print(f"Could not read {file_path}: {e}")

    return documents