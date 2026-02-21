#!/usr/bin/env python3

import argparse
import subprocess
import sys

from packaging.version import Version

# ---------------------------------------------------------
# Utilities
# ---------------------------------------------------------


def run(cmd, capture=True):
    if capture:
        return subprocess.check_output(cmd, text=True).strip()
    else:
        return subprocess.run(cmd)


def is_git_clean():
    status = run(["git", "status", "--porcelain"])
    return status == ""


def get_current_branch():
    return run(["git", "rev-parse", "--abbrev-ref", "HEAD"])


def get_current_version():
    try:
        tag = run(["git", "describe", "--tags", "--abbrev=0"])
        return tag.lstrip("v")
    except subprocess.CalledProcessError:
        return "0.0.0"


def bump(version_str, part):
    v = Version(version_str)

    if part == "major":
        return f"{v.major + 1}.0.0"
    elif part == "minor":
        return f"{v.major}.{v.minor + 1}.0"
    elif part == "patch":
        return f"{v.major}.{v.minor}.{v.micro + 1}"
    else:
        raise ValueError("Invalid bump type")


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Create a semantic version tag for ROOST (dry-run by default)."
    )

    parser.add_argument(
        "part",
        nargs="?",
        choices=["major", "minor", "patch"],
        default="patch",
        help="Version part to bump (default: patch)",
    )

    parser.add_argument("-m", "--message", help="Optional tag message")

    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually create and push the tag (default is dry-run)",
    )

    args = parser.parse_args()

    # -----------------------------------------------------
    # Always compute and show preview first
    # -----------------------------------------------------

    current = get_current_version()
    new_version = bump(current, args.part)
    tag = f"v{new_version}"
    message = args.message or f"{tag}"

    print("\n=== Version Bump Preview ===")
    print(f"Current version : {current}")
    print(f"Bump type       : {args.part}")
    print(f"New version     : {new_version}")
    print(f"Tag to create   : {tag}")
    print(f"Message         : {message}")
    print("============================\n")

    if not args.apply:
        print("🟡 Dry run (default). Use --apply to create and push the tag.")
        return

    # -----------------------------------------------------
    # Safety checks ONLY when applying
    # -----------------------------------------------------

    if not is_git_clean():
        print("❌ Working tree is not clean. Commit or stash changes first.")
        sys.exit(1)

    branch = get_current_branch()
    if branch != "main":
        print(f"❌ Refusing to tag from branch '{branch}'. Switch to 'main'.")
        sys.exit(1)

    # -----------------------------------------------------
    # Run tests before tagging
    # -----------------------------------------------------

    print("🔎 Running test suite before tagging...\n")
    result = subprocess.run(["pytest"])
    if result.returncode != 0:
        print("\n❌ Tests failed. Aborting tag.")
        sys.exit(1)

    # -----------------------------------------------------
    # Create and push tag
    # -----------------------------------------------------

    subprocess.run(["git", "tag", "-a", tag, "-m", message], check=True)
    subprocess.run(["git", "push", "origin", tag], check=True)

    print(f"\n✅ Tagged and pushed {tag}")


if __name__ == "__main__":
    main()
