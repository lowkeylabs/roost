---
title: workflow
---

```
# ---------------------------------------------------------
# 1️⃣ MERGE DEV → MAIN
# ---------------------------------------------------------

git checkout main
git pull origin main      # ensure main is current
git merge dev             # integrate dev
git push origin main


# ---------------------------------------------------------
# 2️⃣ UPDATE OWL PIN ON MAIN AND TEST
# ---------------------------------------------------------

uv run scripts/update_owl_pin.py
uv sync --extra dev
pytest

# If everything passes:

git add pyproject.toml uv.lock
git commit -m "Update OWL pin"
git push origin main


# ---------------------------------------------------------
# 3️⃣ TAG RELEASE (ON MAIN)
# ---------------------------------------------------------

make release          # preview
make release-patch    # or minor / major

# (release script creates tag + pushes tag + reinstalls)


# ---------------------------------------------------------
# 4️⃣ RESYNC DEV WITH MAIN
# ---------------------------------------------------------

git checkout dev
git pull origin dev        # optional but safe
git merge main
git push origin dev
```
