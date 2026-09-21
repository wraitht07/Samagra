import re
from typing import List, Optional

from pydantic import BaseModel

class ExtractedClause(BaseModel):
    clause_id: str
    section: Optional[str] = None
    page: Optional[int] = None
    title: Optional[str] = None
    raw_text: str
    cleaned_requirement: str
    explicit_standards: List[str] = []
    grades_or_parameters: List[str] = []
    certification_demands: List[str] = []
    keywords: List[str] = []

class TenderExtractionResult(BaseModel):
    document_title: str
    summary: str
    total_clauses: int
    clauses: List[ExtractedClause]

# Regex patterns for Indian Standards identification
IS_PATTERN = re.compile(
    r"\bIS\s*[:\s]?\s*([0-9]+(?:\s*\([^\)]+\))?(?:\s*:\s*[0-9]{4})?)",
    re.IGNORECASE,
)
GRADE_PATTERN = re.compile(
    r"\b(Fe\s*415[DS]?|Fe\s*500[DS]?|Fe\s*550[DS]?|Fe\s*600|E250|E350|Grade\s*43|Grade\s*53|OPC\s*43|OPC\s*53|PPC|PSC|M-?Sand|Recycled\s+aggregate|Lithium|Nickel)\b",
    re.IGNORECASE,
)
CERT_PATTERN = re.compile(
    r"\b(ISI\s*Mark|BIS\s*Standard\s*Mark|Scheme-I|Scheme\s*1|CRS|Compulsory\s*Registration\s*Scheme|R-?number|CM/L|Hallmark|Hallmarking|Test\s*Certificate|Lab\s*Report)\b",
    re.IGNORECASE,
)

def normalize_is_id(raw_is: str) -> str:
    """Normalizes variations like 'IS: 456-2000' or 'IS 1786: 2008' to 'IS 456:2000'."""
    clean = re.sub(r"^IS\s*[:\s]*", "IS ", raw_is.strip(), flags=re.IGNORECASE)
    clean = re.sub(r"\s*:\s*", ":", clean)
    clean = re.sub(r"\s*-\s*([0-9]{4})", r":\1", clean)
    clean = re.sub(r"\s*\(part\s*([0-9]+)\)", r" (Part \1)", clean, flags=re.IGNORECASE)
    return clean

def extract_specifications(text_content: str, filename: str = "tender_document.txt") -> TenderExtractionResult:
    """
    Parses tender text into structured requirement clauses with extracted references.
    """
    lines = [line.strip() for line in text_content.splitlines() if line.strip()]

    # Extract document title
    doc_title = "Procurement Specification Document"
    for line in lines[:3]:
        if "SAMPLE TENDER" in line.upper() or "NAME OF WORK:" in line.upper() or "ITEM:" in line.upper():
            doc_title = line.replace("SAMPLE TENDER EXTRACT – ", "").strip()
            break

    # Split text by clause markers
    clause_splits = re.split(
        r"(?=(?:BOQ\s+Clause|Clause|Section|\n\s*\d+\.\s+))",
        text_content,
        flags=re.IGNORECASE,
    )

    extracted_clauses: List[ExtractedClause] = []

    # Fallback: Split by paragraphs if no clause markers found
    if len(clause_splits) <= 1:
        raw_paragraphs = [p.strip() for p in text_content.split("\n\n") if p.strip()]
        if not raw_paragraphs:
            raw_paragraphs = [text_content.strip()]
        clause_splits = raw_paragraphs

    for idx, raw_chunk in enumerate(clause_splits):
        chunk = raw_chunk.strip()
        if not chunk or len(chunk) < 10:
            continue

        # Extract section and title
        section_name = None
        title = None
        first_line = chunk.splitlines()[0].strip()
        if re.match(r"^(?:BOQ\s+Clause|Clause|Section|\d+\.)", first_line, re.IGNORECASE):
            parts = first_line.split("–", 1) if "–" in first_line else first_line.split("-", 1)
            section_name = parts[0].strip()
            title = parts[1].strip() if len(parts) > 1 else section_name

        # Extract IS numbers
        found_is = []
        for m in IS_PATTERN.finditer(chunk):
            full_match = m.group(0)
            norm = normalize_is_id(full_match)
            if norm not in found_is:
                found_is.append(norm)

        # Extract grades/parameters
        found_grades = list({m.group(0).strip() for m in GRADE_PATTERN.finditer(chunk)})

        # Extract certification demands
        found_certs = list({m.group(0).strip() for m in CERT_PATTERN.finditer(chunk)})

        # Extract keywords
        raw_words = re.findall(r"\b[A-Za-z]{4,}\b", chunk)
        stop_words = {
            "shall", "conform", "conforming", "submit", "submitted", "supplier",
            "specification", "requirements", "tender", "sample", "extract",
            "clause", "note", "evaluators",
        }
        keywords = [w.lower() for w in raw_words if w.lower() not in stop_words][:10]

        extracted_clauses.append(
            ExtractedClause(
                clause_id=f"clause_{idx+1:02d}",
                section=section_name or f"Section {idx+1}",
                page=None,  # Removed arbitrary page assignment
                title=title or f"Requirement {idx+1}",
                raw_text=chunk,
                cleaned_requirement=re.sub(r"\s+", " ", chunk),
                explicit_standards=found_is,
                grades_or_parameters=found_grades,
                certification_demands=found_certs,
                keywords=keywords,
            )
        )

    return TenderExtractionResult(
        document_title=doc_title,
        summary=f"Extracted {len(extracted_clauses)} requirement clauses from {filename}.",
        total_clauses=len(extracted_clauses),
        clauses=extracted_clauses,
    )