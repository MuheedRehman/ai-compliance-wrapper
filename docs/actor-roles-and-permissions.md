# Actor Roles and Permissions

The platform supports a Multi-Role Access Control (RBAC) model to ensure separation of duties.

## Roles

### 1. System Admin
*   **Scope:** Full platform access.
*   **Permissions:** Manage users, API keys, integrations, and global settings.

### 2. Compliance Officer / Legal (DPO)
*   **Scope:** Read/Write on compliance metadata; Sign-off authority.
*   **Permissions:** Approve risk classifications, sign Declarations of Conformity, review gap analyses.

### 3. AI Engineer / Developer
*   **Scope:** System Intake and Evidence submission.
*   **Permissions:** Register new AI systems, upload technical documentation, submit model metrics. Cannot approve classifications.

### 4. Product Owner / Business Owner
*   **Scope:** Read/Write on specific owned AI systems.
*   **Permissions:** Define system purpose, map business use cases, assign technical owners.

### 5. External Auditor (Read-Only)
*   **Scope:** Restricted Read-Only access to the Evidence Vault and Reports.
*   **Permissions:** View finalized Technical Documentation, verify cryptographic evidence chains (HMAC), export reports. Cannot modify data.
