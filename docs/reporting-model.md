# Reporting Model

The reporting module formalizes platform data into regulatory-ready artifacts. 

## Report Types

### 1. Technical Documentation Report (Annex IV)
*   **Trigger:** Manual generation prior to system deployment.
*   **Contents:** 
    *   System Description & Intended Purpose
    *   Architecture & Algorithms
    *   Data Provenance & Training Details
    *   Human Oversight Measures
    *   Validation & Testing Metrics
*   **Output Formats:** PDF, Markdown.

### 2. EU Declaration of Conformity (Annex V)
*   **Trigger:** Authorized sign-off by Compliance Officer.
*   **Contents:**
    *   Provider Name & Address
    *   AI System Identification (Version, Name)
    *   Statement of compliance with the EU AI Act
    *   References to harmonized standards applied
*   **Output Formats:** PDF (Cryptographically signed).

### 3. Public Transparency Report
*   **Trigger:** Automated periodic generation (e.g., Annually).
*   **Contents:** High-level summary of deployed AI systems, risk tiers, and general purpose AI disclosures.
*   **Output Formats:** HTML, PDF.

### 4. Internal Gap Analysis Report
*   **Trigger:** On-demand.
*   **Contents:** List of missing evidence, incomplete risk assessments, and non-compliant systems.
*   **Output Formats:** CSV, JSON (for dashboarding).
