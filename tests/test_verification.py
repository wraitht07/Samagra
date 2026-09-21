from src.backend.extraction import extract_specifications
from src.backend.retrieval import retrieval_engine
from src.backend.verification import verification_engine


def test_code_of_practice_trap_is_456():
    sample_text = "BOQ Clause 4.5: All structural concrete shall be ISI marked as per IS 456:2000."
    extraction = extract_specifications(sample_text)
    assert len(extraction.clauses) == 1
    clause = extraction.clauses[0]
    
    candidates = retrieval_engine.retrieve(clause.cleaned_requirement, explicit_standards=clause.explicit_standards)
    verif = verification_engine.verify_clause(clause, candidates)
    
    assert verif.recommended_standard is not None
    assert verif.recommended_standard.standard_id == "IS 456:2000"
    assert "CODE_OF_PRACTICE_MISAPPLIED_AS_PRODUCT" in verif.recommended_standard.traps_detected
    assert verif.recommended_standard.applicability_status == "CODE_OF_PRACTICE_WARNING"

def test_superseded_edition_is_1786_1985():
    sample_text = "Clause 4.3: High strength deformed steel bars conforming to IS 1786:1985 Grade Fe500."
    extraction = extract_specifications(sample_text)
    clause = extraction.clauses[0]
    
    candidates = retrieval_engine.retrieve(clause.cleaned_requirement, explicit_standards=clause.explicit_standards)
    verif = verification_engine.verify_clause(clause, candidates)
    
    assert verif.recommended_standard is not None
    assert verif.recommended_standard.is_superseded is True
    assert "IS 1786:2008" in verif.recommended_standard.current_indexed_edition
    assert any("GRADE_CONFUSION" in t for t in verif.recommended_standard.traps_detected)

def test_mandatory_qco_and_amendments_helmet_is_4151():
    sample_text = "Technical Spec: Helmets shall conform to IS 4151:2015."
    extraction = extract_specifications(sample_text)
    clause = extraction.clauses[0]
    
    candidates = retrieval_engine.retrieve(clause.cleaned_requirement, explicit_standards=clause.explicit_standards)
    verif = verification_engine.verify_clause(clause, candidates)
    
    assert verif.recommended_standard is not None
    assert verif.recommended_standard.is_mandatory is True
    assert "Scheme-I" in verif.recommended_standard.certification_scheme
    assert verif.recommended_standard.amendments_info is not None

