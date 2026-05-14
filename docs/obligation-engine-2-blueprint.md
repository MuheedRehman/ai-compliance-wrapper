# Obligation Engine 2.0 Blueprint

This document preserves the best practices we want to carry forward from the scanner/compliance-engine discussion. It is the implementation guide for Module 4 and should be updated whenever scanner rules, legal mappings, or governance tests change.

Primary legal source of truth:
- EU AI Act Explorer: https://ai-act-service-desk.ec.europa.eu/en/ai-act-explorer
- Official EU AI Act policy page: https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai

Do not copy third-party legal taxonomies directly into the product. Use them as product inspiration only after validating article references and obligations against the official text.

## Best Practices To Keep

### 1. Compliance-Dimension Matrix

Each obligation rule must be represented as a structured compliance dimension, not as free-form text.

Required fields:
- `dimension_id`: stable machine-readable identifier.
- `pillar`: product-facing compliance pillar name.
- `chapter`: EU AI Act chapter or theme.
- `articles`: official article references.
- `annex_refs`: Annex references, when relevant.
- `actor_roles`: provider, deployer, importer, distributor, product manufacturer, authorised representative, or GPAI provider.
- `risk_tiers`: prohibited, high-risk, limited/transparency, GPAI, GPAI systemic risk, minimal/voluntary.
- `trigger_conditions`: exact intake/scanner facts that activate the rule.
- `required_controls`: control templates to materialize.
- `required_evidence`: evidence item types expected in the Evidence Vault.
- `scanner_signals`: website scanner indicators that support or weaken the finding.
- `effective_dates`: application or transition dates to track.
- `confidence_policy`: how confidence is computed and when manual legal review is required.

### 2. Scanner Output Must Map To Obligations

Scanner findings should not stop at "gap found." Each meaningful signal should flow into the compliance workspace:
- scanner signal
- matched obligation dimension
- legal article/annex reference
- generated control
- requested evidence item
- suggested remediation
- report/audit-pack source reference

Example:

```text
Signal: public chatbot, no AI interaction disclosure found
Dimension: transparency-ai-interaction
Article: Article 50
Control: user-facing AI disclosure present
Evidence: screenshot or policy excerpt
Workspace outcome: open gap with source URLs and confidence score
```

### 3. Automated API And Security Tests

Compliance data is sensitive, so every module that touches obligations, evidence, reports, scanner output, or users must have tests for:
- tenant isolation
- required API scopes
- protected route rejection
- unauthorized write rejection
- cross-tenant record access denial
- dashboard live workflow coverage where practical

The live GCP pipeline should keep Playwright E2E checks for the critical happy paths and auth boundaries.

### 4. Modular Rules, Not Hardcoded Legal Text

Obligation rules should be data-driven or isolated in small modules so we can update them as guidance, standards, or implementation dates change.

Rules should produce explainable output:

```text
Because the system is a deployer-operated Annex III employment system,
Article 26 deployer obligations and Article 27 FRIA screening apply.
The platform created controls for human oversight, instructions for use,
monitoring, log retention, and FRIA approval.
```

### 5. Live E2E Tests Stay In The Deployment Pipeline

The GCP deployment pipeline should keep validating the product after deployment:
- API preflight endpoints
- navigation pages
- scanner-to-workspace conversion
- controls
- evidence
- intake/classification
- oversight/incidents/reports/runtime
- authentication redirects and protected behavior

When UI wording changes, update tests to validate the real workflow, not stale labels.

## Core EU AI Act Pillars To Model

These pillars should become first-class dimensions in Module 4:

| Pillar | Official anchor | Product workflow |
| --- | --- | --- |
| AI literacy | Article 4 | Tenant/user training evidence and policy controls |
| Prohibited practices | Article 5 | Intake/scanner red flags, cease/remediate path |
| High-risk classification | Article 6, Annex III | Classification engine and Annex III mapping |
| High-risk requirements | Articles 8-15 | Risk management, data governance, technical documentation, logs, transparency to deployers, human oversight, robustness/cybersecurity |
| Provider obligations | Articles 16-25 | Provider controls, QMS, documentation keeping, logs, corrective action, value-chain responsibilities |
| Deployer obligations | Article 26 | Use according to instructions, human oversight, monitoring, input data relevance, log retention |
| FRIA | Article 27 | Guided FRIA builder, approval workflow, evidence and report output |
| Conformity and registration | Articles 43, 47-49, 71 | Future audit pack, CE/declaration/registration tracking |
| Transparency for certain AI systems | Article 50 | Chatbot/deepfake/synthetic content disclosures and evidence |
| GPAI | Articles 51-56 | GPAI provider obligations, systemic risk path, model documentation and copyright/TDM summaries |
| Post-market monitoring and incidents | Articles 72-73 | Monitoring plan, serious incident workflow, authority notification tracking |
| Remedies and explanations | Articles 85-87 | Complaint handling, right-to-explanation, infringement reporting evidence |

## Acceptance Criteria For Module 4

Module 4 is not "MVP-complete" until it can:
- map an AI system to official article and Annex obligations
- distinguish provider and deployer duties
- explain every obligation in "because X, Y applies" form
- generate control templates and evidence requirements
- attach scanner findings as evidence-backed signals
- track effective dates and manual-review needs
- include test coverage for tenant isolation, scope enforcement, and rule determinism
