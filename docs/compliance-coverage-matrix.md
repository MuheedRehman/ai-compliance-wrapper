# Compliance Coverage Matrix

This matrix maps EU AI Act requirements to current and planned platform features. It is intentionally conservative: "covered" means there is a usable workflow, not just a roadmap idea.

Primary legal source of truth:
- EU AI Act Explorer: https://ai-act-service-desk.ec.europa.eu/en/ai-act-explorer
- Official EU AI Act policy page: https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai

Detailed Module 4 implementation guide: `docs/obligation-engine-2-blueprint.md`.

| EU AI Act area | Requirement | Current platform coverage | Next gap to close |
| :--- | :--- | :--- | :--- |
| Article 4 | AI literacy | Foundation only. Tenant/user roles exist and Evidence Vault can store training evidence. | Add AI literacy controls, training evidence templates, review cadence, and tenant-level completion tracking. |
| Article 5 | Prohibited practices | Partial. Intake has a prohibited-use flag and classification path. | Add prohibited-practice subcategory mapping, mandatory remediation path, and stronger scanner/intake red flags. |
| Article 6 & Annex III | High-risk classification | Partial. Intake and scanner can draft high-risk classification. | Add explicit Annex III category mapping, legal rationale, and confidence/manual-review rules. |
| Articles 8-15 | High-risk requirements | Partial. Controls, evidence, reports, and workspace exist. | Add structured rules for risk management, data governance, technical documentation, logs, instructions, human oversight, robustness, and cybersecurity. |
| Articles 16-25 | Provider obligations | Foundation only. Actor role exists in intake. | Add provider-specific obligation dimensions, QMS controls, conformity path, documentation keeping, corrective action, and value-chain obligations. |
| Article 26 | Deployer obligations | Foundation only. Actor role exists and controls can be created. | Add deployer-specific duties for use according to instructions, monitoring, human oversight, input data relevance, and log retention. |
| Article 27 | FRIA | Basic records only. FRIA endpoints/pages exist. | Build guided FRIA builder, approval workflow, residual risk, and exportable document. |
| Articles 43, 47-49, 71 | Conformity, declaration, registration | Future. Reports exist but no formal conformity workflow. | Add conformity assessment tracker, declaration of conformity, CE marking fields, and EU database registration tracking. |
| Article 50 | Transparency obligations | Partial. Scanner detects disclosure gaps and intake has transparency flags. | Add structured chatbot/deepfake/synthetic-content disclosure controls, evidence requirements, and scanner-to-control mapping. |
| Articles 51-56 | GPAI obligations | Foundation only. Intake can flag GPAI. | Add GPAI provider obligations, systemic-risk route, documentation, policy, evaluation, and copyright/TDM evidence. |
| Articles 72-73 | Post-market monitoring and serious incidents | Partial. Incident records exist. | Add monitoring plan, serious incident classification, regulator notification timers, and status workflow. |
| Articles 85-87 | Remedies, explanations, complaints | Future. | Add appeals/complaints/right-to-explanation workflow and evidence trail. |

## Best Practices Locked In

The following practices are required for future EU AI Act modules:

1. Use a structured compliance-dimension matrix with articles, Annex references, actor roles, triggers, controls, evidence, scanner signals, confidence, and effective dates.
2. Tie scanner findings directly to obligations, controls, evidence requests, and reports.
3. Maintain automated API/security tests for tenant isolation, scopes, protected routes, and cross-tenant access denial.
4. Keep obligation rules modular and explainable instead of embedding one-off legal text in UI components.
5. Preserve live Playwright E2E checks in the GCP deployment pipeline for critical product workflows.
