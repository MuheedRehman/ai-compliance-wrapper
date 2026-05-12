# Product Architecture

## Overview
The EU AI Act Compliance Platform is a modular system designed to manage the lifecycle of AI systems, map regulatory obligations, gather evidence, and generate required compliance reporting.

## Core Modules

### 1. Intake & Discovery Module
*   **Purpose:** Ingests AI system metadata, model cards, and vendor documentation.
*   **Components:** API Intake, Firecrawl Integration (for external policy scraping), Manual Entry Forms.

### 2. Risk Classification Engine
*   **Purpose:** Maps system capabilities against EU AI Act risk tiers (Unacceptable, High-Risk, Limited Risk, Minimal Risk).
*   **Components:** Rules Engine, LLM-Assisted Capability Matching.

### 3. Evidence Vault & Traceability
*   **Purpose:** Stores cryptographic proofs of compliance actions (e.g., risk assessments, audits, logs).
*   **Components:** HMAC Evidence Chain, Document Store.

### 4. Reporting & Export Module
*   **Purpose:** Generates formalized regulatory documents.
*   **Components:** Technical Documentation Generator, Declaration of Conformity builder.

### 5. Dashboard & Monitoring
*   **Purpose:** Provides a centralized view of compliance health, missing controls, and upcoming deadlines.
*   **Components:** Metrics Aggregator, Alerting System.
