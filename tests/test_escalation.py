import pytest

from src.backend.evidence import evidence_engine
from src.backend.extraction import extract_specifications
from src.backend.reasoning import reasoning_engine
from src.backend.retrieval import retrieval_engine
from src.backend.verification import verification_engine


@pytest.mark.asyncio
async def test_case_1_clear_no_ai():
    # Protective helmet standard IS 4151
    text = "Specification: Supply of protective helmets for two-wheeler motor vehicle riders conforming to IS 4151:2015."
    extraction = extract_specifications(text)
    clause = extraction.clauses[0]
    
    candidates = retrieval_engine.retrieve(clause.cleaned_requirement, explicit_standards=clause.explicit_standards)
    verif = verification_engine.verify_clause(clause, candidates)
    reasoning = await reasoning_engine.resolve_ambiguity(clause, verif)
    card = evidence_engine.build_audit_card(clause, verif, reasoning)
    
    assert reasoning.ai_invoked is False
    assert "AI NOT INVOKED" in reasoning.ai_status_label
    assert card.recommended_standard_id == "IS 4151:2015"
    assert card.recommendation_status == "VERIFIED_APPLICABLE"

@pytest.mark.asyncio
async def test_case_2_ambiguous_escalation():
    # Power bank lithium batteries vs nickel
    text = "Specification: Supply of secondary lithium-ion cells and batteries for portable power bank applications."
    extraction = extract_specifications(text)
    clause = extraction.clauses[0]
    
    candidates = retrieval_engine.retrieve(clause.cleaned_requirement, explicit_standards=clause.explicit_standards)
    verif = verification_engine.verify_clause(clause, candidates)
    reasoning = await reasoning_engine.resolve_ambiguity(clause, verif)
    evidence_engine.build_audit_card(clause, verif, reasoning)
    
    assert reasoning.ai_invoked is True
    assert "LOCAL LLM INVOKED" in reasoning.ai_status_label
    assert "Part 2" in (reasoning.resolved_standard_id or "")

@pytest.mark.asyncio
async def test_case_3_insufficient_evidence_human_review():
    # Non-existent false friend valves
    text = "Valves shall conform to IS 1001 / IS 1002 Industrial Valve - General Requirements."
    extraction = extract_specifications(text)
    clause = extraction.clauses[0]
    
    candidates = retrieval_engine.retrieve(clause.cleaned_requirement, explicit_standards=clause.explicit_standards)
    verif = verification_engine.verify_clause(clause, candidates)
    reasoning = await reasoning_engine.resolve_ambiguity(clause, verif)
    card = evidence_engine.build_audit_card(clause, verif, reasoning)
    
    assert card.recommendation_status == "HUMAN_REVIEW_REQUIRED"
    assert reasoning.human_review_required is True
    assert "HUMAN REVIEW REQUIRED" in card.ai_trace["status_label"]

