#!/usr/bin/env python3

import argparse
import subprocess
from pathlib import Path

import tomlkit

REPO_URL = "https://github.com/mdlacasse/Owl.git"
DEPENDENCY_PREFIX = "owlplanner @ git+https://github.com/mdlacasse/Owl.git@"


def get_latest_commit():
    """Return latest commit SHA from GitHub repo."""
    result = subprocess.run(
        ["git", "ls-remote", REPO_URL, "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    sha = result.stdout.split()[0]
    return sha


def update_pyproject(pyproject_path: Path, new_sha: str, dry_run=False):
    text = pyproject_path.read_text()
    doc = tomlkit.parse(text)

    deps = doc["project"]["dependencies"]

    updated = False

    for i, dep in enumerate(deps):
        if isinstance(dep, str) and dep.startswith(DEPENDENCY_PREFIX):
            print(f"Old dependency:\n  {dep}")
            deps[i] = tomlkit.string(f"{DEPENDENCY_PREFIX}{new_sha}")
            updated = True
            break

    if not updated:
        raise RuntimeError("Could not find owlplanner git dependency to update.")

    if dry_run:
        print("\n--- DRY RUN ---")
        print(doc)
        return

    pyproject_path.write_text(tomlkit.dumps(doc))
    print(f"\nUpdated owlplanner to commit {new_sha}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pyproject",
        default="pyproject.toml",
        help="Path to pyproject.toml",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing file",
    )
    args = parser.parse_args()

    pyproject_path = Path(args.pyproject)

    print("Fetching latest commit SHA from Owl repo...")
    sha = get_latest_commit()
    print(f"Latest commit: {sha}")

    update_pyproject(pyproject_path, sha, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
