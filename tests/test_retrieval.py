from src.backend.ingestion import ingestion_manager
from src.backend.retrieval import retrieval_engine


def test_dataset_loaded():
    standards = ingestion_manager.get_all_standards()
    assert len(standards) >= 350
    assert ingestion_manager.get_standard("IS 456:2000") is not None
    assert ingestion_manager.get_standard("IS 1786:2008") is not None
    assert ingestion_manager.get_standard("IS 4151:2015") is not None

def test_exact_retrieval_is_456():
    candidates = retrieval_engine.retrieve(
        query="Plain and reinforced concrete structural design",
        explicit_standards=["IS 456:2000"],
        top_k=5
    )
    assert len(candidates) > 0
    top_ids = [c.standard_id for c in candidates]
    assert "IS 456:2000" in top_ids
    top_cand = candidates[0]
    assert top_cand.standard_id == "IS 456:2000"
    assert top_cand.exact_match is True

def test_bm25_and_semantic_retrieval_helmet():
    candidates = retrieval_engine.retrieve(
        query="Protective helmets for two wheeler riders traffic police head protection",
        top_k=5
    )
    assert len(candidates) > 0
    top_cand = candidates[0]
    assert "4151" in top_cand.standard_id

def test_false_friend_detection():
    # IS 1001 / IS 1002 for industrial valves are false friends in the test dataset
    candidates = retrieval_engine.retrieve(
        query="Industrial valves conforming to IS 1001 / IS 1002",
        explicit_standards=["IS 1001", "IS 1002"],
        top_k=5
    )
    assert len(candidates) > 0
    assert any(c.false_friend_detected for c in candidates)

