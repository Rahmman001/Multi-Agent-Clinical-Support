# Multi-Agent Clinical Support System

> **A team of specialized AI hospital assistants rather than one overloaded chatbot.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-orange.svg)](https://github.com/langchain-ai/langgraph)
[![Pydantic v2](https://img.shields.io/badge/Validation-Pydantic_v2-red.svg)](https://docs.pydantic.dev/)

---

## The Problem It Solves

An Electronic Health Record (EHR) is messy and fragmented. A single patient file often contains:
- 10+ pages of unstructured clinical encounter notes
- 3+ years of dense bloodwork tables
- A list of 12+ active prescriptions
- Vital sign logs (blood pressure, oxygenation, pulse)

If you paste all of that into a single, monolithic ChatGPT-style prompt and ask *"What is wrong with this patient?"*, the model regularly **hallucinates values**, misses subtle contraindications, or gets overwhelmed by noise.

---

## The Multi-Agent Solution

Instead of one AI trying to do everything, the workload is distributed across specialized AI agents that collaborate like an interdisciplinary clinical team:

```
                       ┌──────────────────────┐
                       │ Patient Chart (EHR)  │
                       │    (Synthea JSON)    │
                       └──────────┬───────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         ▼                        ▼                        ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│    Lab Agent    │      │  Pharma Agent   │      │  History Agent  │
│ Scans bloodwork │      │ Checks for drug │      │ Finds recurring │
│ & flag anomalies│      │  interactions   │      │ past conditions │
└────────┬────────┘      └────────┬────────┘      └────────┬────────┘
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  ▼
                       ┌──────────────────────┐
                       │  Lead Triage Agent   │
                       │ Combines findings &  │
                       │ drafts summary card  │
                       └──────────┬───────────┘
                                  ▼
                       ┌──────────────────────┐
                       │  Doctor's Dashboard  │
                       │  (HIGH / MED / LOW)  │
                       └──────────────────────┘
```

### Agent Roles

1. **Lab Agent**: Focuses strictly on quantitative lab panels. Flags anomalies and sudden deltas (*e.g., "Creatinine jumped 40% in two days — possible acute kidney distress"*).
2. **Pharma Agent**: Cross-references active prescriptions with pharmaceutical interaction rules (*e.g., "Drug A + Drug B contraindicated due to severe bleeding risk"*).
3. **History Agent**: Extracts chronic comorbidities and past diagnoses (*e.g., "Patient has a 7-year history of Type 2 Diabetes"*).
4. **Lead Triage Agent (The Coordinator)**: Aggregates findings from all three agents, eliminates duplicates, and computes a composite triage score (**HIGH**, **MEDIUM**, **LOW**) with an executive summary.

---

## Architecture & Engineering Stack (100% Free & Open-Source)

> **Zero Credit Card Required**: Every component in this architecture runs locally or uses generous, no-card-required open tiers.

| Layer | Implementation | Purpose & Cost |
| :--- | :--- | :--- |
| **Data Ingestion** | [Synthea](https://synthetichealth.github.io/synthea/) (JSON) | 100% Free open-source synthetic EHR records (zero HIPAA/PHI risk). |
| **LLM Inference** | **Ollama** (`llama3.2` / `qwen2.5`) | **100% Free & Local** (runs on your Mac GPU/CPU with $0 cost, zero API keys, zero credit card). |
| **Agent Logic** | **LangGraph** (Python) | Free & open-source agent graph state machine with parallel node branching. |
| **Guardrails** | **Pydantic v2** | Open-source JSON schema enforcement guaranteeing deterministic type output. |
| **Dashboard UI** | **Streamlit** (Python) | Open-source, local web dashboard with color-coded risk alerts and drill-down cards. |

---

## Why This Project Stands Out

Most AI applications in the wild are thin prompt wrappers around a single API call. This project demonstrates real **system design**:
* **Separation of Concerns**: Micro-agent architecture where agents have distinct, testable responsibilities.
* **Resilience Against Hallucinations**: Strict type checking and Pydantic validation before data reaches downstream nodes.
* **Deterministic Risk Scoring**: Clear composite heuristics that synthesize multiple clinical signals into an actionable decision.

---

## Detailed Specifications

For complete user stories, functional requirements, and acceptance criteria, view the Product Requirements Document:
* [tasks/prd-multi-agent-clinical-support.md](tasks/prd-multi-agent-clinical-support.md)
