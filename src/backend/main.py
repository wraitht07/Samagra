import json
import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.backend.config import settings
from src.backend.evidence import ProcurementAuditResult, evidence_engine
from src.backend.extraction import extract_specifications
from src.backend.ingestion import ingestion_manager
from src.backend.reasoning import reasoning_engine
from src.backend.retrieval import retrieval_engine
from src.backend.verification import verification_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("samagra.main")

app = FastAPI(
    title="Samagra — Evidence-First Indian Standards Recommendation Engine",
    description=(
        "SIH 26108: Evidence-first recommendation of applicable "
        "Indian Standards for procurement specifications."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure FRONTEND_DIR is a Path object
FRONTEND_DIR = Path(settings.DATA_DIR).parent / "src" / "frontend"

@app.get("/api/health")
def health_check():
    try:
        total_standards = len(ingestion_manager.get_all_standards())
        total_relationships = len(ingestion_manager.relationships_data)
        total_regulations = len(ingestion_manager.regulations_data)
    except AttributeError:
        total_standards = 0
        total_relationships = 0
        total_regulations = 0
    return {
        "status": "healthy",
        "service": "Samagra BIS Decision Support",
        "total_standards": total_standards,
        "total_relationships": total_relationships,
        "total_regulations": total_regulations,
    }

@app.get("/api/sample-tenders")
def get_sample_tenders():
    sample_dir = Path(settings.DATA_DIR) / "sample_tenders"
    samples = []
    if not sample_dir.exists():
        return samples
    for path in sorted(sample_dir.glob("*.txt")):
        with open(path, "r", encoding="utf-8") as file:
            content = file.read()
        samples.append(
            {
                "id": path.stem,
                "filename": path.name,
                "title": path.stem.replace("_", " ").title(),
                "content": content,
            }
        )
    return samples

@app.get("/api/audit-cases")
def get_audit_cases():
    audit_file = Path(settings.DATA_DIR) / "audit_cases.json"
    if not audit_file.exists():
        return []
    with open(audit_file, "r", encoding="utf-8") as file:
        return json.load(file)

@app.get("/api/evaluation-queries")
def get_evaluation_queries():
    evaluation_file = Path(settings.DATA_DIR) / "evaluation_queries.json"
    if not evaluation_file.exists():
        return []
    with open(evaluation_file, "r", encoding="utf-8") as file:
        return json.load(file)

@app.get("/api/standards")
def list_standards(q: str = None, domain: str = None, limit: int = 50):
    standards = ingestion_manager.get_all_standards()
    if domain:
        standards = [
            standard
            for standard in standards
            if standard.get("domain", "").lower() == domain.lower()
        ]
    if q:
        query = q.lower()
        standards = [
            standard
            for standard in standards
            if (
                query in standard.get("standard_id", "").lower()
                or query in standard.get("title", "").lower()
                or query in standard.get("scope", "").lower()
                or any(query in keyword.lower() for keyword in standard.get("keywords", []))
            )
        ]
    return standards[:limit]

@app.post("/api/recommend", response_model=ProcurementAuditResult)
async def process_tender(request: Request, file: UploadFile = None):
    text_to_process = ""
    document_name = "Tender Specification"
    content_type = request.headers.get("content-type", "")

    # JSON request
    if "application/json" in content_type:
        try:
            body = await request.json()
            text_to_process = body.get("text", "")
            document_name = body.get("document_title", "Tender Specification")
        except (json.JSONDecodeError, ValueError) as error:
            logger.debug("JSON body parse notice: %s", error)

    # Multipart / form request
    elif "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
        form = await request.form()
        if "text" in form:
            text_to_process = str(form.get("text", ""))
            document_name = form.get("document_title", "Tender Specification")
        elif "file" in form:
            uploaded = form["file"]
            if getattr(uploaded, "filename", None):
                document_name = uploaded.filename
                content = await uploaded.read()
                try:
                    text_to_process = content.decode("utf-8")
                except UnicodeDecodeError:
                    text_to_process = content.decode("latin-1", errors="ignore")

    # Fallback body parsing
    if not text_to_process:
        raw_body = await request.body()
        if raw_body:
            try:
                body = json.loads(raw_body.decode("utf-8"))
                text_to_process = body.get("text", "")
                document_name = body.get("document_title", "Tender Specification")
            except (json.JSONDecodeError, UnicodeDecodeError):
                text_to_process = raw_body.decode("utf-8", errors="ignore")

    if not text_to_process.strip():
        raise HTTPException(status_code=400, detail="No tender specification text or file provided.")

    # Evidence-first processing pipeline
    extraction_result = await run_in_threadpool(
        extract_specifications, text_to_process, filename=document_name
    )

    audit_cards = []
    for clause in extraction_result.clauses:
        candidates = await run_in_threadpool(
            retrieval_engine.retrieve,
            query=clause.cleaned_requirement,
            explicit_standards=clause.explicit_standards,
            top_k=settings.TOP_K_RETRIEVAL,
        )
        verification = await run_in_threadpool(
            verification_engine.verify_clause, clause, candidates
        )
        reasoning = await reasoning_engine.resolve_ambiguity(clause, verification)
        audit_card = evidence_engine.build_audit_card(clause, verification, reasoning)
        audit_cards.append(audit_card)
    return evidence_engine.synthesize_document_result(extraction_result, audit_cards)
if FRONTEND_DIR.exists():
    app.mount(
        "/static",
        StaticFiles(directory=str(FRONTEND_DIR), html=True),
        name="static",
    )

@app.get("/")
async def serve_index():
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "Samagra API running. Frontend static file not found."}