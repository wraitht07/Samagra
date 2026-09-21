# Implementation Plan — SIH 26108: Evidence-First Indian Standards Recommendation Engine

A lightweight, offline-first procurement decision-support system designed to identify and verify applicable Indian Standards (IS) for tender requirements, with an uncompromising evidence-first audit trail.

---

## 1. User Review Required

> [!IMPORTANT]
> **Database & Local Services**
> - **PostgreSQL + pgvector**: A local pgvector container (`pgvector/pgvector:pg16` on port 5432) or local Postgres instance will store the 360 curated BIS standards with 1024-dim BGE-M3 vector embeddings, BM25 keyword tokens, and metadata. An in-memory/SQLite fallback with exact vector cosine indexing is also built into the backend configuration so the system can run seamlessly under any local environment constraints.
> - **Local LLM Escalation**: If Ollama or a local OpenAI-compatible endpoint is available (e.g. `qwen2.5:1.5b` / `llama3.2:1b`), the escalation layer connects directly to it. If offline or no LLM daemon is running, a deterministic fallback resolver grounded strictly in the retrieved evidence dataset ensures the pipeline completes with transparent "AI NOT INVOKED" or evidence-backed resolution.
> - **Offline & Privacy**: No data leaves the local machine. All embeddings, text extraction, retrieval, and verification run strictly locally.

---

## 2. Proposed Architecture & Module Breakdown

The implementation strictly follows the non-negotiable repository structure and data flow:

```
Samagra
│
├── src/
│   ├── frontend/
│   │   ├── index.html        # Clean, government-grade Evidence-First UI
│   │   ├── styles.css        # Restrained, high-contrast, accessible UI design
│   │   └── app.js            # Interactive trace, document analysis, tender samples
│   │
│   └── backend/
│       ├── main.py           # FastAPI endpoints (/api/recommend, /api/audit, /api/standards, /api/health)
│       ├── config.py         # App settings, DB URI, model names, threshold params
│       ├── ingestion.py      # Ingests standards.json, relationships.json, regulations.json to DB
│       ├── extraction.py     # Deterministic tender parser & requirement extractor
│       ├── retrieval.py      # Exact IS matching + BM25 + BGE-M3 vector search + RRF fusion & reranking
│       ├── verification.py   # Normative check, edition/supersession, QCO/scheme checks, trap detection
│       ├── reasoning.py      # Local LLM escalation layer (evidence-grounded prompt, strict guardrails)
│       └── evidence.py       # Evidence trail synthesizer (trace milestones, citations, audit badges)
│
├── data/
│   ├── standards.json        # 360 curated BIS standards
│   ├── relationships.json    # Supersedes, test methods, normative, safety relationships
│   ├── regulations.json      # QCOs, CROs, Hallmarking orders
│   ├── evaluation_queries.json # 10 evaluation benchmarks
│   ├── audit_cases.json      # 10 defect/audit traps
│   └── sample_tenders/       # Concrete, valves false-friend, helmets
│
├── scripts/
│   ├── ingest_standards.py   # CLI tool to run DB ingestion and precompute BGE-M3 embeddings
│   └── sync_standards.py     # Integrity check & dataset verification script
│
├── tests/
│   ├── test_retrieval.py     # Exact, BM25, semantic, RRF, and false-friend tests
│   ├── test_verification.py  # Lifecycle, supersession, code-vs-product, QCO status checks
│   └── test_escalation.py    # Clear case (no LLM), ambiguous (LLM), insufficient evidence tests
│
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 3. Detailed Component Plan

### A. Environment & Dependencies (`requirements.txt`, `.env.example`)
- **FastAPI + Uvicorn**: High-performance asynchronous API server.
- **SQLAlchemy + psycopg2-binary + pgvector**: Vector and relational querying.
- **Sentence-Transformers (BAAI/bge-m3)** or lightweight multi-lingual semantic model with CPU optimization + caching.
- **rank-bm25**: Fast in-memory/DB BM25 retrieval for technical codes and nomenclature.
- **Pytest**: Comprehensive test suite.

### B. Ingestion & Database Schema (`src/backend/ingestion.py`, `scripts/ingest_standards.py`)
- Tables:
  - `standards`: `standard_id` (PK), `title`, `status`, `standard_type`, `publication_year`, `revision`, `scope`, `domain`, `certification_type`, `certification_mandatory`, `certification_basis`, `certification_source`, `keywords`, `nasty_flag`, `notes`, `verified`, `source`, `embedding` (vector(1024)).
  - `relationships`: `from_standard`, `to_standard`, `type` (supersedes, normative_reference, test_method, safety, related_code_vs_product, sibling_parts), `note`.
  - `regulations`: `regulation_id`, `title`, `ministry`, `effective_from`, `standards_covered`, `scheme`, `notes`.
- Hybrid storage: PostgreSQL + pgvector as primary; in-memory fallback mirror for instant zero-dependency testing.

### C. Extraction & Normalization (`src/backend/extraction.py`)
- Parse tender text / uploaded documents into discrete procurement requirement clauses.
- Extract referenced IS numbers (e.g. `IS 456:2000`, `IS 1786`, `IS:4151`), grades (e.g. `Fe500`, `Fe500D`, `OPC 43`), product keywords, and compliance demands (`ISI Mark`, `CRS`, `Hallmark`).

### D. Exact + Hybrid Retrieval & RRF Reranking (`src/backend/retrieval.py`)
- **Step 1 - Exact/Code Match**: Find exact IS standard ID references.
- **Step 2 - Lexical Retrieval (BM25)**: Score standards on title, scope, keywords, and domain.
- **Step 3 - Dense Vector Retrieval (BGE-M3)**: Embed requirement query and compute cosine distance against standard scopes.
- **Step 4 - Reciprocal Rank Fusion (RRF)**: Combine lexical and dense ranks via \( RRF(d) = \sum \frac{1}{k + r(d)} \).
- **Step 5 - Domain & Precision Reranking**: Boost matches matching product keywords, grades, and domain.

### E. Verification & Lifecycle Engine (`src/backend/verification.py`)
- **Code vs Product Trap Detection**: Identify if standard is a `code_of_practice` incorrectly demanded as a product with ISI mark (e.g., IS 456).
- **Supersession & Edition Check**: Check if requested year is superseded (e.g. `IS 1786:1985` -> `IS 1786:2008`, `IS 302 (Part 1):2008` -> `2024`).
- **CRS vs ISI Mark Scheme Verification**: Check if product falls under MeitY CRO (requires R-number, not CM/L ISI mark) or Hallmarking.
- **Related Standards Enrichment**: Pull normative references, test methods, safety standards from `relationships.json`.
- **Regulatory / QCO Status**: Check `regulations.json` for mandatory compliance dates and ministry orders. Default to `NOT DETERMINED` when missing.

### F. Escalation & Reasoning Layer (`src/backend/reasoning.py`)
- Deterministic ambiguity detector:
  - If single unambiguous match with verified applicability -> **AI NOT INVOKED**.
  - If multiple candidate standards compete with semantic trade-offs -> **LOCAL LLM INVOKED** with strict prompt containing only retrieved candidates.
  - If top scores below confidence threshold and no exact match -> **HUMAN REVIEW REQUIRED** (zero hallucination).

### G. Evidence Synthesis (`src/backend/evidence.py`)
- Synthesizes the full audit trail:
  - Exact requirement quote + page/clause citation.
  - Recommendation status: `VERIFIED APPLICABLE`, `SUPERSEDED`, `CODE OF PRACTICE (NOT PRODUCT)`, `AMBIGUOUS / MULTI-PART`, `INSUFFICIENT EVIDENCE`.
  - Step-by-step recommendation trace milestones.
  - Related standards broken down by type: Test Methods, Safety, Normative, Installation.

### H. Evidence-First Web UI (`src/frontend/`)
- Professional procurement layout with three main sections:
  1. **Specification Ingestion Panel**: Direct text input, file upload, pre-configured sample cases (Clear, Ambiguous, False-friend Insufficient Evidence, Audit Cases).
  2. **Interactive Recommendation Trace**: Real-time progress indicators showing every pipeline stage.
  3. **Evidence Cards & Audit Dashboard**: Highlighting recommended standards, citations, traps detected, regulatory notes, and allied standards.

### I. Automated Tests (`tests/`)
- `test_retrieval.py`: Exact ID lookups, BM25 keywords, dense vectors, RRF fusion, false-friend non-retrieval.
- `test_verification.py`: Supersession detection, code-vs-product warnings, CRS vs ISI mark checks.
- `test_escalation.py`: Clear case (no LLM), ambiguous case (escalated), false-friend (human review required).

---

## 4. Verification Plan

### Automated Tests
```bash
venv/bin/pytest tests/ -v
```

### End-to-End Demo Scenarios Verification
1. **Case 1 (Clear)**: Run `sample_tenders/protective_helmet_tender.txt` -> Verifies IS 4151:2015, mentions QCO 2020, amendments 1 & 2, ISI mark Scheme-I, "AI NOT INVOKED".
2. **Case 2 (Ambiguous)**: Query "Which standard for lithium-ion battery power bank cells vs nickel cells" -> Detects Part 1 vs Part 2 ambiguity, invokes LLM / local reasoning, isolates IS 16046 (Part 2):2018 CRS.
3. **Case 3 (Insufficient Evidence)**: Run `sample_tenders/industrial_valve_tender.txt` ("IS 1001 / IS 1002") -> Detects non-existent false friend, yields "HUMAN REVIEW REQUIRED", does not hallucinate.
