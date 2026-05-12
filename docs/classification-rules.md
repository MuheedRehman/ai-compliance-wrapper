# AI Act Classification & Intake Engine (Phase 3D)

## Purpose
The Intake Engine provides a deterministic, rule-based framework for classifying AI systems under the EU AI Act. It collects structured data from users to determine their legal role, the system's risk category, and the resulting obligation path.

## Input Fields Collected
The following fields are captured during the intake wizard:
- `title`: A user-friendly name for the assessment record.
- `is_developer`: Boolean indicating if the actor is a Provider.
- `is_deployer`: Boolean indicating if the actor is a Deployer.
- `is_prohibited_use`: Boolean indicating practices forbidden under Article 5.
- `is_high_risk_annex_iii`: Boolean indicating use cases listed in Annex III.
- `is_safety_component`: Boolean indicating systems used as safety components in regulated products.
- `has_transparency_obligation`: Boolean indicating systems like chatbots or deepfakes (Article 52).
- `is_gpai`: Boolean indicating General Purpose AI models.

## Actor Role Determination
- **Provider**: If `is_developer` is true.
- **Deployer**: If `is_deployer` is true (and not a provider).
- **Importer/Distributor**: Fallback if neither of the above are explicitly selected.

## System Classification Logic
The engine evaluates inputs in a specific order of precedence:
1. **Prohibited AI System**: Triggered by `is_prohibited_use`.
2. **High-Risk AI System**: Triggered by `is_high_risk_annex_iii` or `is_safety_component`.
3. **General Purpose AI (GPAI)**: Triggered by `is_gpai`.
4. **Limited Risk AI System**: Triggered by `has_transparency_obligation`.
5. **Minimal Risk AI System**: Default state if no other criteria are met.

## Obligation Paths
- `CEASE_AND_DESIST`: Assigned to Prohibited systems.
- `FULL_COMPLIANCE_ART_16`: Assigned to High-Risk systems where the actor is a **Provider**.
- `OPERATIONAL_GOVERNANCE_ART_29`: Assigned to High-Risk systems where the actor is a **Deployer**.
- `GPAI_COMPLIANCE_ART_51_52`: Assigned to GPAI models.
- `TRANSPARENCY_ART_52`: Assigned to Limited Risk systems.
- `VOLUNTARY_CODE_OF_CONDUCT`: Assigned to Minimal Risk systems.

## Data Persistence
Results are stored in the `intake_assessments` table, scoped by `tenant_id`. This output is designed to be consumed by:
- **Phase 3E (Readiness)**: To map specific obligations to checklist items.
- **Phase 4 (Reporting)**: To populate the legal classification section of compliance reports.
- **FRIA Workflow**: To trigger mandatory Impact Assessments for High-Risk systems.
