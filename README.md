# 🚀 Samagra — Evidence-First Indian Standards Recommendation Engine

**📌 SIH 26108: AI-Powered Recommendation Engine for Identifying Applicable Indian Standards (IS) for Procurement Specifications.**

Samagra is a **lightweight, offline-first** procurement decision-support system designed to assist procurement officials in **identifying, verifying, and auditing Indian Standards (IS)** for technical specifications, BOQ clauses, and natural language requirements.

✅ **Evidence-First** | 🏛️ **Public Safety Compliant**

---

## 🏗️ System Architecture

Samagra strictly implements an **Evidence-First** pipeline where the **LLM is only the last escalation layer** for resolving semantic ambiguities:

```
TENDER / SPECIFICATION
        ↓
INGESTION (Curated BIS Corpus — 360 Standards)
        ↓
SPECIFICATION EXTRACTION
        ↓
EXACT / KEYWORD RETRIEVAL
        ↓
HYBRID RETRIEVAL (BM25 + BGE-M3 Dense Embeddings)
        ↓
RRF (Reciprocal Rank Fusion)
        ↓
RERANKING & FILTERING
        ↓
APPLICABILITY / RELATIONSHIP VERIFICATION
        ↓
VERSION / AMENDMENT CHECK
        ↓
REGULATORY / CERTIFICATION CHECK (QCOs, CROs, Hallmarking)
        ↓
AMBIGUITY DETECTED?
     /        \
   NO          YES
   ↓            ↓
EVIDENCE    LOCAL LLM
                ↓
             EVIDENCE
                ↓
    PROCUREMENT AUDIT RESULT

```

### 🔑 Core Architecture Principles

* **📜 Evidence > Inference**: Recommendations are **strictly grounded** in indexed standards, active editions, and statutory Quality Control Orders.
* **🤖 AI As Last Escalation**: If deterministic evidence is clear, **`AI NOT INVOKED`**.
* **❌ Zero Hallucination**: If an unverified or false-friend standard is referenced, the system flags **`HUMAN REVIEW REQUIRED`** rather than inventing BIS numbers.
* **🛡️ Public Safety & Executive Dossier**: For every recommendation, provides senior authorities with **statutory justification, previous amendment history, and public safety rationale**. No arbitrary similarity percentages or confidence scores.

---

## 📁 Repository Structure

```
Samagra
│
├── src/
│   ├── frontend/               # 🌐 Clean, accessible Government/Procurement UI
│   │   ├── index.html         # 📄 High-contrast, restrained styling
│   │   ├── styles.css         # 🎨 CSS for professional UI
│   │   └── app.js             # ⚡ Interactive pipeline trace, dossier cards, demo scenarios
│   │
│   └── backend/                # 🐍 FastAPI + Python Backend
│       ├── main.py            # 🚀 FastAPI server & endpoints
│       ├── config.py          # ⚙️ Configuration & thresholds
│       ├── ingestion.py       # 📥 Dataset loading & PostgreSQL / in-memory sync
│       ├── extraction.py      # 🔍 Specification & clause extraction engine
│       ├── retrieval.py       # 🔎 Exact + BM25 + BGE-M3 + RRF hybrid search
│       ├── verification.py    # ✅ Lifecycle, traps, QCO, and public safety verification
│       ├── reasoning.py       # 🤖 Local LLM escalation layer (evidence-grounded)
│       └── evidence.py        # 📋 Evidence synthesis & Executive Audit Dossier
│
├── data/                       # 📊 Curated Datasets
│   ├── standards.json         # 📚 360 cleaned, curated Indian Standards
│   ├── relationships.json     # 🔗 Supersession, normative, test, and safety relationships
│   ├── regulations.json       # 📜 Quality Control Orders (QCOs) & CROs
│   ├── evaluation_queries.json # 📝 10 evaluation benchmarks
│   ├── audit_cases.json       # 🔍 10 tender defect / trap scenarios
│   └── sample_tenders/        # 📄 Concrete test cases (valves, false-friend, helmets)
│
├── scripts/                    # 🛠️ Utility Scripts
│   ├── ingest_standards.py    # 📥 Database ingestion CLI
│   └── sync_standards.py      # 🔄 Read-only dataset consistency validator
│
├── tests/                      # 🧪 Test Suite
│   ├── test_retrieval.py      # 🔎 Retrieval unit tests
│   ├── test_verification.py   # ✅ Lifecycle & trap detection tests
│   └── test_escalation.py     # 🤖 Case 1, Case 2, and Case 3 tests
│
├── requirements.txt           # 📦 Python Dependencies
├── .env.example               # 🔐 Environment Variables Template
├── .gitignore                 # 🚫 Git Ignore Rules
└── README.md                  # 📖 Project Documentation

```

---

## 🎯 Demonstration Scenarios

Samagra includes **3 deliberately distinct outcomes** in the UI to showcase its capabilities:

### 🟢 **CASE 1 — Clear Specification (✅ AI NOT INVOKED)**

* **📄 Sample**: Protective Helmets (`IS 4151:2015`)
* **🎯 Outcome**:
* Exact statutory match.
* Active edition.
* Mandatory **Scheme-I ISI Mark** per **Helmet QCO 2020**.
* Includes **Amendments 1 & 2**.



### 🟡 **CASE 2 — Semantic Ambiguity (🤖 LOCAL LLM INVOKED)**

* **📄 Sample**: Portable Power Bank Secondary Cells (`IS 16046 (Part 2)` vs `IS 16046 (Part 1)`)
* **🎯 Outcome**:
* Ambiguity detected between **Lithium (Part 2)** vs **Nickel (Part 1)** chemistry.
* Escalates to **local LLM** to verify and ground in **CRS R-number**.



### 🔴 **CASE 3 — Insufficient Evidence / False-Friend (⚠️ HUMAN REVIEW REQUIRED)**

* **📄 Sample**: Industrial Valves (`IS 1001 / IS 1002`)
* **🎯 Outcome**:
* Identifies **non-existent standard reference**.
* Blocks defect.
* Declares **`HUMAN REVIEW REQUIRED`**.



---

## ⚡ Quick Start & Execution

### 📋 Prerequisites

* **Python 3.9+** virtual environment.
* **Optional**: PostgreSQL with `pgvector` (containerized via `pgvector/pgvector:pg16`) or **in-memory fallback**.

---

### 🚀 Running the Application

#### 1️⃣ Activate Virtual Environment

```bash
# Linux/macOS
source venv/bin/activate  

# Windows
.\venv\Scripts\activate

```

#### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt

```

#### 3️⃣ Download Local Models (BGE-M3)

Samagra uses `BAAI/bge-m3` for dense embeddings. Download and set it up locally:

```bash
# Create local model directory
mkdir -p models

# Download model via Hugging Face CLI
huggingface-cli download BAAI/bge-m3 --local-dir models/bge-m3

```

> **Note:** Update `src/backend/config.py` to point to the local path: `MODEL_PATH = "models/bge-m3"`.

#### 4️⃣ Ingest Standards Dataset (Optional DB Sync)

```bash
python scripts/ingest_standards.py

```

#### 5️⃣ Start FastAPI Application

```bash
uvicorn src.backend.main:app --host 0.0.0.0 --port 8000 --reload

```

---

## 🧪 Testing & Execution Verification

Run the entire unit and escalation test suite:

```bash
pytest tests/ -v

```

---

## 📊 System Performance & Technical Stack

### 🔍 Current Execution Profile (In-Memory Mode)

* **Dataset**: 360 standards, 12 relationships, 7 regulations loaded from JSON.
* **Retrieval Engine**: Sparse (BM25) + Dense (1024-dim BGE-M3) vector search joined via Reciprocal Rank Fusion (RRF).
* **Embedding Performance**:
* Initial batch processing: `~40.52 it/s`
* Subsequent / Peak optimized batches: `~70.05` to `~75.29 it/s`


* **Fallback**: Automatic switch to lightweight in-memory mode if PostgreSQL + `pgvector` instance is unattached.

### 🛠️ Technical Stack

| Component | Technology | Purpose |
| --- | --- | --- |
| **Backend** | FastAPI (Python 3.9+) | REST API & Pipeline Orchestration |
| **Frontend** | Vanilla JS + HTML/CSS | Lightweight, accessible UI |
| **Database** | PostgreSQL + pgvector | Persistent storage (optional) |
| **Retrieval** | BM25 + BGE-M3 + RRF | Hybrid search (sparse + dense) |
| **Embeddings** | BAAI/bge-m3 | 1024-dimensional dense vectors |
| **LLM (Local)** | Ollama / Llama / Mistral | Grounded fallback for ambiguity resolution |
| **Testing** | Pytest | Unit & integration test execution |
| **Linting** | Ruff + ESLint | Code quality & style enforcement |

---

## 📜 License & Disclaimer

* **License**: MIT (Open Source)
* **Compliance**: Aligned with Indian Government Procurement Standards and Bureau of Indian Standards (BIS) framework.
* **Disclaimer**: Samagra is an automated decision-support engine. All critical procurement audits must be cross-verified against official BIS publication releases.
