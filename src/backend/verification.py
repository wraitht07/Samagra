import logging
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from src.backend.config import settings
from src.backend.extraction import ExtractedClause
from src.backend.ingestion import ingestion_manager
from src.backend.retrieval import RetrievalCandidate

logger = logging.getLogger("sparkrit.verification")

class StandardApplicabilityResult(BaseModel):
    standard_id: str
    title: str
    applicability_status: str  # "VERIFIED_APPLICABLE", "SUPERSEDED", "CODE_OF_PRACTICE_WARNING", "FALSE_FRIEND_REJECTED", "AMBIGUOUS"
    applicability_reasons: List[str]
    is_superseded: bool = False
    superseded_by: Optional[str] = None
    supersedes: Optional[str] = None
    current_indexed_edition: Optional[str] = None
    amendments_info: Optional[str] = None
    amendment_history_notes: Optional[str] = None
    certification_scheme: Optional[str] = None  # "Scheme-I (ISI Mark)", "CRS (R-number)", "Hallmarking", None
    is_mandatory: Optional[bool] = None
    qco_order: Optional[str] = None
    ministry: Optional[str] = None
    effective_date: Optional[str] = None
    related_standards: Dict[str, Any] = {
        "normative_references": [],
        "test_methods": [],
        "safety_standards": [],
        "superseded": [],
        "allied_codes": [],
    }
    raw_metadata: Dict[str, Any] = {}

class ClauseVerificationResult(BaseModel):
    clause_id: str
    section: Optional[str] = None
    requirement_summary: str
    recommended_standard: Optional[StandardApplicabilityResult] = None
    alternative_candidates: List[StandardApplicabilityResult] = []
    ambiguity_detected: bool = False
    ambiguity_reason: Optional[str] = None
    insufficient_evidence: bool = False
    requires_human_review: bool = False

class VerificationEngine:
    """
    Verifies retrieved candidate standards against procurement clauses,
    validating lifecycle, relationships, and regulatory checks.
    """

    def __init__(self):
        self.ingestion = ingestion_manager

    def _get_relationships_for(self, standard_id: str) -> List[Dict[str, Any]]:
        """Fallback-safe wrapper for ingestion_manager.get_relationships_for."""
        try:
            return self.ingestion.get_relationships_for(standard_id)
        except (AttributeError, TypeError):
            logger.warning(f"No get_relationships_for method for {standard_id}")
            return []

    def _get_regulations_for(self, standard_id: str) -> List[Dict[str, Any]]:
        """Fallback-safe wrapper for ingestion_manager.get_regulations_for."""
        try:
            return self.ingestion.get_regulations_for(standard_id)
        except (AttributeError, TypeError):
            logger.warning(f"No get_regulations_for method for {standard_id}")
            return []

    def _get_standard(self, standard_id: str) -> Optional[Dict[str, Any]]:
        """Fallback-safe wrapper for ingestion_manager.get_standard."""
        try:
            return self.ingestion.get_standard(standard_id)
        except (AttributeError, TypeError):
            logger.warning(f"No get_standard method for {standard_id}")
            return None

    def verify_candidate(
        self,
        candidate: RetrievalCandidate,
        clause: ExtractedClause,
    ) -> StandardApplicabilityResult:
        std_id = candidate.standard_id
        std_data = self._get_standard(std_id) or candidate.candidate_metadata

        # Handle non-existent / false-friend candidate
        if candidate.false_friend_detected or not std_data or std_data.get("standard_type") == "unknown":
            return StandardApplicabilityResult(
                standard_id=std_id,
                title=candidate.title,
                applicability_status="FALSE_FRIEND_REJECTED",
                applicability_reasons=[
                    f"Standard '{std_id}' does not exist in the BIS corpus.",
                    "Rejecting non-existent standard reference.",
                ],
                certification_scheme=None,
                related_standards={
                    "normative_references": [],
                    "test_methods": [],
                    "safety_standards": [],
                    "superseded": [],
                    "allied_codes": [],
                },
                raw_metadata=std_data or {},
            )

        title = std_data.get("title", candidate.title)
        std_type = std_data.get("standard_type", "product_standard")

        applicability_reasons: List[str] = []
        status = "VERIFIED_APPLICABLE"

        # 1. Applicability: Code of Practice vs Product Standard
        if std_type == "code_of_practice":
            if any("ISI" in cert.upper() for cert in clause.certification_demands) or "ISI" in clause.raw_text.upper():
                status = "CODE_OF_PRACTICE_WARNING"
                applicability_reasons.append(
                    f"WARNING: {std_id} is a Code of Practice, not a product standard. ISI Mark is invalid for CoP."
                )
            else:
                applicability_reasons.append(f"Applicable as {std_type}.")

        # 2. Version / Supersession Check
        is_superseded = False
        superseded_by = None
        supersedes = None
        current_indexed_edition = std_id

        rels = self._get_relationships_for(std_id)
        for r in rels:
            if r.get("type") == "superseded_by" and r.get("from") == std_id:
                is_superseded = True
                superseded_by = r.get("to")
                status = "SUPERSEDED"
                applicability_reasons.append(f"Superseded by {superseded_by}.")
            elif r.get("type") == "supersedes" and r.get("from") == std_id:
                supersedes = r.get("to")
                applicability_reasons.append(f"Supersedes {supersedes}.")

        # Check for outdated year in tender
        for explicit in clause.explicit_standards:
            if explicit.startswith(std_id.split(":")[0]) and ":" in explicit:
                cited_year = explicit.split(":")[-1]
                indexed_year = str(std_data.get("publication_year", ""))
                if cited_year != indexed_year:
                    try:
                        if int(cited_year or 0) < int(indexed_year or 9999):
                            is_superseded = True
                            applicability_reasons.append(
                                f"Tender cites outdated year {cited_year}. Current: {std_id}."
                            )
                    except ValueError:
                        logger.warning(f"Invalid year format: {cited_year} or {indexed_year}")

        # 3. Amendment Check (from dataset)
        amendments_info = std_data.get("amendments")
        amendment_history_notes = std_data.get("amendment_history")

        # 4. Regulatory & Certification Check
        cert_info = std_data.get("certification") or {}
        cert_scheme = cert_info.get("type")
        is_mandatory = cert_info.get("mandatory")
        qco_order = cert_info.get("source")
        ministry = None
        effective_date = None

        regs = self._get_regulations_for(std_id)
        if regs:
            reg = regs[0]
            cert_scheme = reg.get("scheme", cert_scheme)
            qco_order = reg.get("title", qco_order)
            ministry = reg.get("ministry")
            effective_date = reg.get("effective_from")
            is_mandatory = True
            applicability_reasons.append(
                f"Mandatory under {qco_order} ({ministry}, Effective: {effective_date})."
            )
        elif cert_info.get("basis") == "not_uniformly_mandatory":
            cert_scheme = None
            is_mandatory = None
            applicability_reasons.append("Certification: NOT DETERMINED.")

        # 5. Scheme Mismatch Check
        if cert_scheme:
            if "CRS" in cert_scheme and (
                any("ISI" in cert.upper() for cert in clause.certification_demands)
                or "ISI" in clause.raw_text.upper()
            ):
                applicability_reasons.append(
                    "Scheme mismatch: CRS requires R-number, not ISI Mark."
                )

            if "Hallmarking" in cert_scheme and any(
                "ISI" in cert.upper() for cert in clause.certification_demands
            ):
                applicability_reasons.append(
                    "Scheme mismatch: Hallmarking required, not ISI Mark."
                )

        # 6. Group Related Standards
        related_stds: Dict[str, Any] = {
            "normative_references": [],
            "test_methods": [],
            "safety_standards": [],
            "superseded": [],
            "allied_codes": [],
        }

        for r in rels:
            target = r.get("to") if r.get("from") == std_id else r.get("from")
            rtype = r.get("type", "allied_codes")
            note = r.get("note", "")

            entry = {"standard": target, "note": note, "type": rtype}
            if rtype in ["normative_reference", "normative"]:
                related_stds["normative_references"].append(entry)
            elif rtype in ["test_method", "test"]:
                related_stds["test_methods"].append(entry)
            elif rtype in ["safety_standard", "safety"]:
                related_stds["safety_standards"].append(entry)
            elif rtype in ["supersedes", "superseded_by"]:
                related_stds["superseded"].append(entry)
            else:
                related_stds["allied_codes"].append(entry)

        return StandardApplicabilityResult(
            standard_id=std_id,
            title=title,
            applicability_status=status,
            applicability_reasons=applicability_reasons,
            is_superseded=is_superseded,
            superseded_by=superseded_by,
            supersedes=supersedes,
            current_indexed_edition=current_indexed_edition,
            amendments_info=amendments_info,
            amendment_history_notes=amendment_history_notes,
            certification_scheme=cert_scheme,
            is_mandatory=is_mandatory,
            qco_order=qco_order,
            ministry=ministry,
            effective_date=effective_date,
            related_standards=related_stds,
            raw_metadata=std_data,
        )

    def verify_clause(
        self,
        clause: ExtractedClause,
        candidates: List[RetrievalCandidate],
    ) -> ClauseVerificationResult:
        if not candidates:
            return ClauseVerificationResult(
                clause_id=clause.clause_id,
                section=clause.section,
                requirement_summary=clause.cleaned_requirement,
                recommended_standard=None,
                alternative_candidates=[],
                ambiguity_detected=False,
                insufficient_evidence=True,
                requires_human_review=True,
            )

        verified_candidates = [self.verify_candidate(c, clause) for c in candidates]

        top_cand = candidates[0]
        if (
            top_cand.false_friend_detected
            or verified_candidates[0].applicability_status == "FALSE_FRIEND_REJECTED"
        ):
            return ClauseVerificationResult(
                clause_id=clause.clause_id,
                section=clause.section,
                requirement_summary=clause.cleaned_requirement,
                recommended_standard=verified_candidates[0],
                alternative_candidates=verified_candidates[1:5],
                ambiguity_detected=False,
                insufficient_evidence=True,
                requires_human_review=True,
            )

        # Ambiguity check: Close RRF scores or sibling parts
        ambiguity_detected = False
        ambiguity_reason = None

        if len(candidates) >= 2:
            top_rrf = candidates[0].rrf_score
            second_rrf = candidates[1].rrf_score
            std1_id = candidates[0].standard_id
            std2_id = candidates[1].standard_id

            if "Part 1" in std1_id and "Part 2" in std2_id and std1_id.split("(")[0] == std2_id.split("(")[0]:
                ambiguity_detected = True
                ambiguity_reason = f"Sibling parts detected: {std1_id} vs {std2_id}."
            elif abs(top_rrf - second_rrf) < settings.AMBIGUITY_SCORE_DELTA_THRESHOLD and top_cand.rrf_score < 0.25:
                ambiguity_detected = True
                ambiguity_reason = f"Close scores: {std1_id} vs {std2_id}."

        insufficient_evidence = False
        requires_human_review = False
        if (
            top_cand.rrf_score < settings.MIN_CONFIDENCE_THRESHOLD
            and not top_cand.exact_match
        ):
            insufficient_evidence = True
            requires_human_review = True

        return ClauseVerificationResult(
            clause_id=clause.clause_id,
            section=clause.section,
            requirement_summary=clause.cleaned_requirement,
            recommended_standard=verified_candidates[0],
            alternative_candidates=verified_candidates[1:5],
            ambiguity_detected=ambiguity_detected,
            ambiguity_reason=ambiguity_reason,
            insufficient_evidence=insufficient_evidence,
            requires_human_review=requires_human_review,
        )

verification_engine = VerificationEngine()