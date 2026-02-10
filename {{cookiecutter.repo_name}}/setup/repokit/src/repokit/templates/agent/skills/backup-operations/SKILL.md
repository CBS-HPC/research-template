---
name: backup-operations
description: Manage backup remotes and data sync with repokit-backup commands and verification checks.
---

# backup-operations

## Workflow
1. Configure remote:
   - repokit-backup add --remote <remote>
2. Push:
   - repokit-backup push --remote <remote>
3. Pull (recovery/testing):
   - repokit-backup pull --remote <remote>
4. Compare state:
   - repokit-backup diff --remote <remote>

## Verify
- Remote config exists and secrets are not committed.
- Diff output is reviewed before destructive operations.
