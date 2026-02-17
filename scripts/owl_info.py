#!/usr/bin/env python3
"""
Print information about the active owlplanner installation.

Shows:
- Import path
- Whether it is local (editable) or installed
- If local: git branch + commit
- If installed: version
"""

import inspect
import pathlib
import subprocess
import sys


def main():
    try:
        import owlplanner
    except ImportError:
        print("❌ owlplanner not importable")
        sys.exit(1)

    path = pathlib.Path(inspect.getfile(owlplanner)).resolve()
    print(f"OWL import path: {path}")

    # Detect if local repo (editable)
    repo_root = None
    if "site-packages" not in str(path):
        for parent in [path] + list(path.parents):
            if (parent / ".git").exists():
                repo_root = parent
                break

    if repo_root:
        print("Mode: LOCAL (editable)")
        try:
            branch = (
                subprocess.check_output(
                    ["git", "branch", "--show-current"],
                    cwd=repo_root,
                )
                .decode()
                .strip()
            )

            commit = (
                subprocess.check_output(
                    ["git", "rev-parse", "--short", "HEAD"],
                    cwd=repo_root,
                )
                .decode()
                .strip()
            )

            dirty = (
                subprocess.check_output(
                    ["git", "status", "--porcelain"],
                    cwd=repo_root,
                )
                .decode()
                .strip()
            )

            print(f"Branch: {branch}")
            print(f"Commit: {commit}")
            print(f"Dirty: {'YES' if dirty else 'NO'}")

        except Exception as e:
            print("⚠️  Could not determine git info:", e)

    else:
        print("Mode: INSTALLED (site-packages)")
        try:
            from owlplanner import __version__

            print(f"Version: {__version__}")
        except Exception:
            pass


if __name__ == "__main__":
    main()
