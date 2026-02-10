---
name: readme-sync
description: Regenerate README via repokit and then apply project-specific edits so docs match actual project behavior.
---

# readme-sync

## Workflow
1. Run repokit readme.
2. Post-edit README.md for project-specific accuracy:
   - align terminology with domain and methods
   - remove irrelevant boilerplate
   - ensure command examples are valid in this repo
   - ensure package/tool names match current CLI names
3. Recheck links and anchors.

## Verify
- README.md has no stale command names.
- All edited sections reflect current code and folder layout.
