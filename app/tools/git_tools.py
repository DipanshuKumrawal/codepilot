from pathlib import Path
from git import Repo


BASE_REPOSITORY_DIR = Path("./data/repositories")


def clone_repository(repository_url: str):

    BASE_REPOSITORY_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    repository_name = (
        repository_url
        .rstrip("/")
        .split("/")[-1]
    )

    if repository_name.endswith(".git"):
        repository_name = repository_name[:-4]

    destination = (
        BASE_REPOSITORY_DIR /
        repository_name
    )

    if destination.exists():
        print(
            f"[Git] Repository already exists: "
            f"{destination}"
        )

        return str(destination)

    print(
        f"[Git] Cloning {repository_url}"
    )

    Repo.clone_from(
        repository_url,
        destination
    )

    print(
        f"[Git] Cloned to {destination}"
    )

    return str(destination)