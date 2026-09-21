import logging  # noqa: I001
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from src.backend.extraction import ExtractedClause, TenderExtractionResult
from src.backend.reasoning import LLMReasoningOutput
from src.backend.verification import ClauseVerificationResult, StandardApplicabilityResult

logger = logging.getLogger("sparkrit.evidence")

class EvidenceAuditCard(BaseModel):
    clause_id: str
    section: Optional[str]
    page: Optional[int]

    extracted_requirement: str

    recommendation_status: str
    recommended_standard_id: Optional[str]
    standard_title: Optional[str]

    applicability_checks: List[str]
    related_standards: Dict[str, Any]  # Simplified from nested Dict

    version_info: Dict[str, Any]
    regulatory_check: Dict[str, Any]

    ai_trace: Dict[str, Any]
    trace_milestones: List[str]

class ProcurementAuditResult(BaseModel):
    document_title: str
    total_clauses: int

    clear_count: int
    ambiguous_count: int
    human_review_count: int

    cards: List[EvidenceAuditCard]
    summary_trace: List[str]

class EvidenceSynthesisEngine:
    """
    Converts extraction, verification, and reasoning outputs into
    an evidence-first procurement result.
    """

    def build_audit_card(
        self,
        clause: ExtractedClause,
        verification: ClauseVerificationResult,
        reasoning: LLMReasoningOutput,
    ) -> EvidenceAuditCard:
        milestones = [
            "✓ Document extracted",
            f"✓ Requirement identified ({clause.section or 'Clause'})",
            "✓ Standards retrieved",
        ]

        if verification.recommended_standard:
            milestones.append("✓ Applicability verified")
            milestones.append("✓ Version & amendment checked")
            milestones.append("✓ Regulatory check completed")
        else:
            milestones.append("⚠ No sufficiently supported standard identified")

        if reasoning.human_review_required:
            milestones.append("⚠ INSUFFICIENT EVIDENCE → HUMAN REVIEW REQUIRED")
        elif reasoning.ai_invoked:
            milestones.append(f"⚠ Semantic ambiguity detected ({reasoning.escalation_reason})")
            milestones.append(f"→ LOCAL LLM INVOKED ({reasoning.ai_status_label})")
            milestones.append("✓ Explanation grounded in retrieved evidence")
        else:
            milestones.append("— AI NOT INVOKED (Deterministic Evidence Sufficient)")

        # Resolve target standard
        target_std: Optional[StandardApplicabilityResult] = verification.recommended_standard
        if (
            reasoning.resolved_standard_id
            and target_std
            and target_std.standard_id != reasoning.resolved_standard_id
        ):
            for alternative in verification.alternative_candidates:
                if alternative.standard_id == reasoning.resolved_standard_id:
                    target_std = alternative
                    break

        # Handle insufficient evidence
        if not target_std or reasoning.human_review_required:
            recommendation_status = "HUMAN_REVIEW_REQUIRED"
            standard_id = None
            standard_title = "Human Review Required"
            applicability_checks = [
                "No sufficiently supported Indian Standard was identified for this requirement."
            ]
            related_standards = {
                "normative_references": [],
                "test_methods": [],
                "safety_standards": [],
                "superseded": [],
                "allied_codes": [],
            }
            version_info = {
                "indexed_record": "NOT DETERMINED",
                "publication_year": "NOT DETERMINED",
                "revision": "NOT DETERMINED",
                "amendment": "NOT DETERMINED",
                "superseded_status": "NOT DETERMINED",
            }
            regulatory_check = {
                "certification_scheme": "NOT DETERMINED",
                "mandatory": "NOT DETERMINED",
                "qco_order": "NOT DETERMINED",
            }
        else:
            recommendation_status = target_std.applicability_status
            standard_id = target_std.standard_id
            standard_title = target_std.title
            applicability_checks = target_std.applicability_reasons
            related_standards = target_std.related_standards

            version_info = {
                "indexed_record": target_std.current_indexed_edition or standard_id,
                "publication_year": target_std.raw_metadata.get("publication_year", "NOT DETERMINED"),
                "revision": target_std.raw_metadata.get("revision", "NOT DETERMINED"),
                "is_superseded": target_std.is_superseded,
                "superseded_by": target_std.superseded_by,
                "supersedes": target_std.supersedes,
                "amendment": target_std.amendments_info or "NOT DETERMINED",
                "amendment_history": target_std.amendment_history_notes or "NOT DETERMINED",
            }
            regulatory_check = {
                "certification_scheme": target_std.certification_scheme,
                "mandatory": (
                    "MANDATORY"
                    if target_std.is_mandatory
                    else ("NON-MANDATORY" if target_std.is_mandatory is False else "NOT DETERMINED")
                ),
                "qco_order": target_std.qco_order or "NOT DETERMINED",
                "ministry": target_std.ministry or "NOT DETERMINED",
                "effective_date": target_std.effective_date or "NOT DETERMINED",
            }

        ai_trace = {
            "ai_invoked": reasoning.ai_invoked,
            "status_label": reasoning.ai_status_label,
            "escalation_reason": reasoning.escalation_reason or "NONE",
            "reasoning_explanation": reasoning.reasoning_explanation or "NONE",
        }

        return EvidenceAuditCard(
            clause_id=clause.clause_id,
            section=clause.section,
            page=clause.page,
            extracted_requirement=clause.cleaned_requirement,
            recommendation_status=recommendation_status,
            recommended_standard_id=standard_id,
            standard_title=standard_title,
            applicability_checks=applicability_checks,
            related_standards=related_standards,
            version_info=version_info,
            regulatory_check=regulatory_check,
            ai_trace=ai_trace,
            trace_milestones=milestones,
        )

    def synthesize_document_result(
        self,
        extraction: TenderExtractionResult,
        cards: List[EvidenceAuditCard],
    ) -> ProcurementAuditResult:
        clear_count = sum(
            1 for card in cards if not card.ai_trace["ai_invoked"] and card.recommendation_status != "HUMAN_REVIEW_REQUIRED"
        )
        ambiguous_count = sum(1 for card in cards if card.ai_trace["ai_invoked"])
        human_review_count = sum(1 for card in cards if card.recommendation_status == "HUMAN_REVIEW_REQUIRED")

        summary_trace = [
            f"Analyzed {len(cards)} procurement specification clauses from '{extraction.document_title}'",
            f"{clear_count} clauses resolved without AI escalation",
            f"{ambiguous_count} clauses required local AI reasoning",
            f"{human_review_count} clauses require human review",
        ]

        return ProcurementAuditResult(
            document_title=extraction.document_title,
            total_clauses=len(cards),
            clear_count=clear_count,
            ambiguous_count=ambiguous_count,
            human_review_count=human_review_count,
            cards=cards,
            summary_trace=summary_trace,
        )

evidence_engine = EvidenceSynthesisEngine()