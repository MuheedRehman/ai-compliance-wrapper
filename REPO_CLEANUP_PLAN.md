# Repository Cleanup Plan

Last updated: 2026-05-14

## Decision

The canonical working repo is:

```text
D:\AI_Compliance\Backend\Sprint6B_Migrations_Postgres_CI\backend
```

The outer folder is:

```text
D:\AI_Compliance\Backend\Sprint6B_Migrations_Postgres_CI
```

The outer folder currently contains a second Git repository and duplicate project files. That is misleading and should be cleaned up carefully.

## Findings

### Active repo

`backend/.git` is the real project repo.

- Branch: `main`
- Remote: `origin` -> `https://github.com/MuheedRehman/ai-compliance-wrapper.git`
- Recent commits exist, including tenant admin and Cloud Build work.
- Current untracked files are project-memory docs:
  - `MODULE_ROADMAP_RECOVERY.md`
  - `WORK_TRACKER.md`
  - `REPO_CLEANUP_PLAN.md`

### Misleading outer repo

The outer `.git` repository appears to be accidental or obsolete.

- It has no useful remote configured.
- It has no committed project history.
- It stages duplicate top-level copies of `apps/`, `docs/`, `infra/`, `Dockerfile`, and `cloudbuild.yaml`.
- It makes `git status` from the outer folder look very different from the active project status.

### Duplicate files

Outer `docs/` matches `backend/docs/`.

Outer `apps/`, `infra/`, `Dockerfile`, `cloudbuild.yaml`, `.dockerignore`, and `.gitignore` differ from the backend repo. They should be treated as an archive or stale duplicate until we decide otherwise.

Notable outer duplicate differences:

- `apps/dashboard/package.json`
- `apps/dashboard/package-lock.json`
- `apps/dashboard/STAGING_DEPLOYMENT.md`
- `apps/dashboard/app/globals.css`
- `apps/dashboard/app/layout.tsx`
- `apps/dashboard/app/(app)/layout.tsx`
- Several older dashboard detail pages only present in outer `apps/`
- `apps/dashboard/lib/auth.ts`
- `infra/terraform/main.tf`
- `infra/terraform/outputs.tf`
- `infra/terraform/variables.tf`
- Root `Dockerfile`
- Root `cloudbuild.yaml`

### Ignored local/generated files in active repo

These are ignored and should not be committed:

- `.env`
- `venv/`
- `.pytest_cache/`
- `__pycache__/`
- `app/data/*.db`
- `uvicorn*.log`
- `apps/dashboard/node_modules/`
- `apps/dashboard/.next/`
- `apps/dashboard/test-results/`
- `infra/terraform/.terraform/`
- `infra/terraform/*.tfstate`
- `infra/terraform/tfplan`

## Safe Cleanup Phases

### Phase 1: Lock the project memory

Commit these files inside the active `backend` repo:

- `MODULE_ROADMAP_RECOVERY.md`
- `WORK_TRACKER.md`
- `REPO_CLEANUP_PLAN.md`

Goal: preserve the roadmap and current module status before any cleanup.

### Phase 2: Stop using the outer Git repo

Recommended action after approval:

- Archive or remove the outer `.git` folder so `git status` from the outer folder stops showing misleading staged duplicate files.

Safer option:

- Rename outer `.git` to `_archive_outer_git_2026-05-14`.

Cleaner option:

- Delete outer `.git`.

### Phase 3: Archive or remove outer duplicate project files

Recommended action after approval:

- Archive the outer duplicate shell into `_archive_outer_duplicate_2026-05-14`, or delete it after verifying nothing valuable exists only in the outer copy.

Candidates:

- `app/`
- `apps/`
- `docs/`
- `infra/`
- root `Dockerfile`
- root `cloudbuild.yaml`
- root `.dockerignore`
- root `.gitignore`

Do not remove `backend/`.

### Phase 4: Optional local artifact cleanup

This is optional. These files are ignored, so they are not damaging Git status inside `backend`, but removing them can reduce disk noise.

Candidates:

- Python caches: `__pycache__/`, `.pytest_cache/`
- Logs: `uvicorn*.log`, `test_out.txt`
- Local DBs: `app/data/*.db`
- Next.js build output: `apps/dashboard/.next/`
- Playwright results: `apps/dashboard/test-results/`
- Terraform local state: `infra/terraform/*.tfstate`, `infra/terraform/.terraform/`, `infra/terraform/tfplan`

Usually keep unless disk cleanup is needed:

- `venv/`
- `apps/dashboard/node_modules/`

## Post-Cleanup Checks

Run from `backend`:

```powershell
git status --short
pytest
alembic heads
```

Run from `backend/apps/dashboard` if frontend was touched:

```powershell
npm run lint
npm run build
```

## Cleanup Rule

Do not delete or move files from the outer folder until the active `backend` repo has a clean committed checkpoint.
