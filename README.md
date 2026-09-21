# 🚀 Samagra — Evidence-First Indian Standards Recommendation Engine

**📌 SIH 26108: AI-Powered Recommendation Engine for Identifying Applicable Indian Standards (IS) for Procurement Specifications.**

Samagra is a **lightweight, offline-first** procurement decision-support system designed to assist procurement officials in **identifying, verifying, and auditing Indian Standards (IS)** for technical specifications, BOQ clauses, and natural language requirements.

✅ **Evidence-First**| 🏛️ **Public Safety Compliant**

---

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
     /       \
   NO         YES
   ↓           ↓
EVIDENCE     LOCAL LLM
               ↓
            EVIDENCE
               ↓
   PROCUREMENT AUDIT RESULT
```
### 🔑 Core Architecture Principles:
- **📜 Evidence > Inference**: Recommendations are **strictly grounded** in indexed standards, active editions, and statutory Quality Control Orders.
- **🤖 AI As Last Escalation**: If deterministic evidence is clear, **`AI NOT INVOKED`**.
- **❌ Zero Hallucination**: If an unverified or false-friend standard is referenced, the system flags **`HUMAN REVIEW REQUIRED`** rather than inventing BIS numbers.
- **🛡️ Public Safety & Executive Dossier**: For every recommendation, provides senior authorities with **statutory justification, previous amendment history, and public safety rationale**. No arbitrary similarity percentages or confidence scores.

---

---

## 📁 Repository Structure
Samagra
│
├── src/
│   ├── frontend/               # 🌐 Clean, accessible Government/Procurement UI
│   │   ├── index.html         # 📄 High-contrast, restrained styling
│   │   ├── styles.css         # 🎨 CSS for professional UI
│   │   └── app.js             # ⚡ Interactive pipeline trace, dossier cards, demo scenarios
│   │
│   └── backend/               # 🐍 FastAPI + Python Backend
│       ├── main.py            # 🚀 FastAPI server & endpoints
│       ├── config.py          # ⚙️ Configuration & thresholds
│       ├── ingestion.py       # 📥 Dataset loading & PostgreSQL / in-memory sync
│       ├── extraction.py      # 🔍 Specification & clause extraction engine
│       ├── retrieval.py       # 🔎 Exact + BM25 + BGE-M3 + RRF hybrid search
│       ├── verification.py    # ✅ Lifecycle, traps, QCO, and public safety verification
│       ├── reasoning.py       # 🤖 Local LLM escalation layer (evidence-grounded)
│       └── evidence.py        # 📋 Evidence synthesis & Executive Audit Dossier
│
├── data/                      # 📊 Curated Datasets
│   ├── standards.json         # 📚 360 cleaned, curated Indian Standards
│   ├── relationships.json     # 🔗 Supersession, normative, test, and safety relationships
│   ├── regulations.json       # 📜 Quality Control Orders (QCOs) & CROs
│   ├── evaluation_queries.json # 📝 10 evaluation benchmarks
│   ├── audit_cases.json       # 🔍 10 tender defect / trap scenarios
│   └── sample_tenders/        # 📄 Concrete test cases (valves, false-friend, helmets)
│
├── scripts/                   # 🛠️ Utility Scripts
│   ├── ingest_standards.py    # 📥 Database ingestion CLI
│   └── sync_standards.py      # 🔄 Read-only dataset consistency validator
│
├── tests/                     # 🧪 Test Suite
│   ├── test_retrieval.py      # 🔎 Retrieval unit tests
│   ├── test_verification.py   # ✅ Lifecycle & trap detection tests
│   └── test_escalation.py     # 🤖 Case 1, Case 2, and Case 3 tests
│
├── requirements.txt           # 📦 Python Dependencies
├── .env.example               # 🔐 Environment Variables Template
├── .gitignore                 # 🚫 Git Ignore Rules
└── README.md                  # 📖 This File

---

---

## 🎯 Demonstration Scenarios

Samagra includes **3 deliberately distinct outcomes** in the UI to showcase its capabilities:

---

### 🟢 **CASE 1 — Clear Specification (✅ AI NOT INVOKED)**
- **📄 Sample**: Protective Helmets (`IS 4151:2015`)
- **🎯 Outcome**:
  - Exact statutory match.
  - Active edition.
  - Mandatory **Scheme-I ISI Mark** per **Helmet QCO 2020**.
  - Includes **Amendments 1 & 2**.

---

### 🟡 **CASE 2 — Semantic Ambiguity (🤖 LOCAL LLM INVOKED)**
- **📄 Sample**: Portable Power Bank Secondary Cells (`IS 16046 (Part 2)` vs `IS 16046 (Part 1)`)
- **🎯 Outcome**:
  - Ambiguity detected between **Lithium (Part 2)** vs **Nickel (Part 1)** chemistry.
  - Escalates to **local LLM** to verify and ground in **CRS R-number**.

---

### 🔴 **CASE 3 — Insufficient Evidence / False-Friend (⚠️ HUMAN REVIEW REQUIRED)**
- **📄 Sample**: Industrial Valves (`IS 1001 / IS 1002`)
- **🎯 Outcome**:
  - Identifies **non-existent standard reference**.
  - Blocks defect.
  - Declares **`HUMAN REVIEW REQUIRED`**.

---

---

## ⚡ Quick Start & Execution

### 📋 Prerequisites
- **Python 3.9+** virtual environment.
- **Optional**: PostgreSQL with `pgvector` (containerized via `pgvector/pgvector:pg16`) or **in-memory fallback**.

---

### 🚀 Running the Application

#### 1️⃣ Activate Virtual Environment
```bash
source venv/bin/activate  # Linux/macOS
.\venv\Scripts\activate   # Windows
2️⃣ Install Dependencies
pip install -r requirements.txt
3️⃣ Download Local Models (BGE-M3)
Samagra uses BAAI/bge-m3 for dense embeddings. To download and set it up:
# Create a directory for models (optional)
mkdir -p models

# Download BGE-M3 using Hugging Face CLI
huggingface-cli download BAAI/bge-m3 --local-dir models/bge-m3
🌍 OS-Specific Setup
| **OS** | **Command** |
| --- | --- |
| **Linux** | `huggingface-cli download BAAI/bge-m3 --local-dir models/bge-m3` |
| **macOS** | `huggingface-cli download BAAI/bge-m3 --local-dir models/bge-m3` |
| **Windows** | `huggingface-cli download BAAI/bge-m3 --local-dir models\bge-m3` |

# Example: Update config.py to point to the local model
MODEL_PATH = "models/bge-m3"
4️⃣ Ingest Standards Dataset (Optional DB Sync)
python scripts/ingest_standards.py
5️⃣ Start FastAPI Application
uvicorn src.backend.main\:app --host 0.0.0.0 --port 8000 --reload
🧪 Running the Test Suite
pytest tests/ -v

📊 System Performance & Logs
🔍 Current Setup (In-Memory Mode)
✅ Dataset: 360 standards, 12 relationships, 7 regulations loaded from JSON.
🔎 Retrieval:BM25 Index: Initialized over 360 standards.
Dense Embeddings: TF-IDF matrix (360, 4096) + BGE-M3 embeddings (360, 1024).

🤖 Model: BAAI/bge-m3 (replaced all-MiniLM-L6-v2).
💾 Fallback: PostgreSQL not detected → In-memory mode enabled.
⚡ Embedding Generation Performance
Batch Processing Speed:~40.52 it/s (Initial batch)
~67.36 it/s (Subsequent batches)
~70.05 it/s (Optimized batches)
~75.29 it/s (Peak performance)

Note: Performance varies based on CPU/GPU and batch size. BGE-M3 is slower but more accurate than all-MiniLM-L6-v2.
🛠️ Technical Stack
| **Component** | **Technology** | **Purpose** |
| --- | --- | --- |
| **Backend** | FastAPI (Python 3.9+) | REST API & Pipeline Orchestration |
| **Frontend** | Vanilla JS + HTML/CSS | Lightweight, accessible UI |
| **Database** | PostgreSQL + pgvector | Persistent storage (optional) |
| **Retrieval** | BM25 + BGE-M3 + RRF | Hybrid search (sparse + dense) |
| **Embeddings** | BAAI/bge-m3 | 1024-dimensional dense vectors |
| **LLM (Local)** | Any local LLM (e.g., Mistral, Llama) | Ambiguity resolution (evidence-grounded) |
| **Testing** | Pytest | Unit & integration tests |
| **Linting** | Ruff + ESLint | Code quality & style enforcement |
📜 License & Compliance
📜 License: MIT (Open Source)
🏛️ Compliance: Designed for Indian Government Procurement Standards (BIS).
⚠️ Disclaimer: This is a decision-support prototype. Always validate recommendations with official BIS documents.

🤝 Contributing
Contributions are welcome! Please follow these steps:
-Fork the repository.
-Create a branch (git checkout -b feature/your-feature).
-Commit your changes (git commit -m "Add your feature").
-Push to the branch (git push origin feature/your-feature).
-Open a Pull Request.


🚀 Built with for Indian Procurement Officials | 🏛️ Evidence-First







