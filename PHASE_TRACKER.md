# AI Governance Platform - Phase Tracker

## Completed Phases

### Phase 1: Core AI Registry & Evidence Base
- **Goal:** Establish the foundational AI System registry and linkable evidence models.
- **Status:** **COMPLETED**
- **Key Features:**
  - `AiSystem` CRUD endpoints.
  - Basic feature mapping.
  - Extensible evidence linking.

### Phase 2: System-Centric Refactoring
- **Goal:** Move from feature-centric to system-centric compliance workflows.
- **Status:** **COMPLETED**
- **Key Features:**
  - Refactored relationships.
  - Data backfill logic and state reconciliation.
  - Clean phase boundaries established.

### Phase 3: Runtime Evidence Linkage
- **Goal:** Strict tenant isolation and validate-before-mutate logic for AI features.
- **Status:** **COMPLETED**
- **Key Features:**
  - `deployment_status` and `registration_status` literals.
  - Strict `tenant_id` isolation.
  - End-to-end runtime evidence linkage tests passed.

### Phase 0A: Cloud Foundation (Infrastructure)
- **Goal:** Establish robust infrastructure foundation for staging and production on GCP.
- **Status:** **COMPLETED**
- **Key Features:**
  - `cloudbuild.yaml` setup with explicit build gates (`_CLOUD_SQL_INSTANCE`).
  - Production PostgreSQL connection pooling (`pool_size=5`, `max_overflow=10`).
  - Cloud Run secret injection (via env vars) and max-instance limits to prevent DB exhaustion.
  - Isolated SQLite fallback for local backward compatibility.
  - Verified infrastructure unit tests avoiding module reload side-effects.

## Next Up
- **Phase 0B:** IAM & Staging Rollout Verification.
- **Phase 4:** Governance Assessments (FRIA, Oversight, Incident management).
