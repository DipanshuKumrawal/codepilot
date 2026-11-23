from pathlib import Path
import difflib


def _safe_path(repo_path, file_path):
    """Resolve file_path inside repo_path; return None if it escapes."""

    repo = Path(repo_path).resolve()
    full = (repo / file_path).resolve()

    if full != repo and repo not in full.parents:
        return None

    return full


def create_diff(
    repo_path,
    file_path,
    new_content
):
    """Build a unified diff. New files are allowed (diff vs empty)."""

    full_path = _safe_path(repo_path, file_path)

    if full_path is None:
        return {
            "success": False,
            "message": "Path is outside the repository."
        }

    is_new = not full_path.exists()

    if not is_new and not full_path.is_file():
        return {
            "success": False,
            "message": "Path is not a file."
        }

    old_content = "" if is_new else full_path.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    diff = "".join(
        difflib.unified_diff(
            old_content.splitlines(True),
            new_content.splitlines(True),
            fromfile="/dev/null" if is_new else file_path,
            tofile=file_path
        )
    )

    added = sum(
        1 for l in diff.splitlines()
        if l.startswith("+") and not l.startswith("+++")
    )
    removed = sum(
        1 for l in diff.splitlines()
        if l.startswith("-") and not l.startswith("---")
    )

    return {
        "success": True,
        "file": file_path,
        "diff": diff,
        "old_content": old_content,
        "new_content": new_content,
        "is_new": is_new,
        "added": added,
        "removed": removed
    }


def apply_change(
    repo_path,
    file_path,
    new_content,
    backup=True
):
    """Write new content. Keeps a .bak copy of the original."""

    full_path = _safe_path(repo_path, file_path)

    if full_path is None:
        return False

    try:
        if backup and full_path.exists():
            Path(str(full_path) + ".bak").write_text(
                full_path.read_text(
                    encoding="utf-8",
                    errors="ignore"
                ),
                encoding="utf-8"
            )

        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(new_content, encoding="utf-8")

    except OSError:
        return False

    return True


def undo_change(repo_path, file_path):
    """Restore the file from its .bak copy. Returns True on success."""

    full_path = _safe_path(repo_path, file_path)

    if full_path is None:
        return False

    backup = Path(str(full_path) + ".bak")

    if not backup.exists():
        return False

    full_path.write_text(
        backup.read_text(encoding="utf-8", errors="ignore"),
        encoding="utf-8"
    )
    backup.unlink()

    return True


def propose_change(repo_path, file_path, new_content):
    return create_diff(
        repo_path,
        file_path,
        new_content
    )
