# tests/test_verification.py
import pytest
from src.backend.extraction import ExtractedClause
from src.backend.retrieval import RetrievalCandidate
from src.backend.verification import verification_engine, StandardApplicabilityResult

@pytest.fixture
def sample_clause():
    return ExtractedClause(
        clause_id="clause_01",
        section="Section 1",
        page=1,
        title="Test Clause",
        raw_text="Helmets shall conform to IS 4151:2015 and bear ISI Mark.",
        cleaned_requirement="Helmets shall conform to IS 4151:2015 and bear ISI Mark.",
        explicit_standards=["IS 4151:2015"],
        grades_or_parameters=[],
        certification_demands=["ISI Mark"],
        keywords=["helmets", "conform", "ISI", "Mark"]
    )

@pytest.fixture
def sample_candidate():
    return RetrievalCandidate(
        standard_id="IS 4151:2015",
        title="Protective Helmets for Two-Wheeler Riders",
        candidate_metadata={"standard_type": "product_standard", "publication_year": "2015"},
        rrf_score=0.95,
        exact_match=True,
        false_friend_detected=False
    )

@pytest.fixture
def sample_candidate_false_friend():
    return RetrievalCandidate(
        standard_id="IS 9999:2000",
        title="Non-Existent Standard",
        candidate_metadata={"standard_type": "unknown"},
        rrf_score=0.1,
        exact_match=False,
        false_friend_detected=True
    )

def test_code_of_practice_trap_is_456(sample_clause):
    candidate = RetrievalCandidate(
        standard_id="IS 456:2000",
        title="Plain and Reinforced Concrete - Code of Practice",
        candidate_metadata={"standard_type": "code_of_practice", "publication_year": "2000"},
        rrf_score=0.9,
        exact_match=True,
        false_friend_detected=False
    )
    clause = ExtractedClause(
        clause_id="clause_01",
        section="Section 1",
        page=1,
        title="Test Clause",
        raw_text="Concrete shall conform to IS 456:2000 and bear ISI Mark.",
        cleaned_requirement="Concrete shall conform to IS 456:2000 and bear ISI Mark.",
        explicit_standards=["IS 456:2000"],
        grades_or_parameters=[],
        certification_demands=["ISI Mark"],
        keywords=["concrete", "conform", "ISI", "Mark"]
    )
    result = verification_engine.verify_candidate(candidate, clause)
    assert result.applicability_status == "CODE_OF_PRACTICE_WARNING"
    assert any("Code of Practice" in reason for reason in result.applicability_reasons)

def test_superseded_edition_is_1786_1985(sample_clause):
    candidate = RetrievalCandidate(
        standard_id="IS 1786:1985",
        title="Hot Rolled Steel Bars for Concrete Reinforcement",
        candidate_metadata={"standard_type": "product_standard", "publication_year": "1985"},
        rrf_score=0.85,
        exact_match=True,
        false_friend_detected=False
    )
    clause = ExtractedClause(
        clause_id="clause_01",
        section="Section 1",
        page=1,
        title="Test Clause",
        raw_text="Steel bars shall conform to IS 1786:1985.",
        cleaned_requirement="Steel bars shall conform to IS 1786:1985.",
        explicit_standards=["IS 1786:1985"],
        grades_or_parameters=[],
        certification_demands=[],
        keywords=["steel", "bars", "conform"]
    )
    result = verification_engine.verify_candidate(candidate, clause)
    assert result.is_superseded == True
    assert result.superseded_by is not None

def test_mandatory_qco_and_amendments_helmet_is_4151(sample_clause):
    candidate = RetrievalCandidate(
        standard_id="IS 4151:2015",
        title="Protective Helmets for Two-Wheeler Riders",
        candidate_metadata={
            "standard_type": "product_standard",
            "publication_year": "2015",
            "certification": {"type": "Scheme-I (ISI Mark)", "mandatory": True, "source": "Helmet QCO 2020"}
        },
        rrf_score=0.95,
        exact_match=True,
        false_friend_detected=False
    )
    result = verification_engine.verify_candidate(candidate, sample_clause)
    assert result.certification_scheme == "Scheme-I (ISI Mark)"
    assert result.is_mandatory == True
    assert result.qco_order == "Helmet QCO 2020"