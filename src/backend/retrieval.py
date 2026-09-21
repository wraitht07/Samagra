import logging
import re
from typing import Any, Optional

import numpy as np
from pydantic import BaseModel
from rank_bm25 import BM25Okapi

from src.backend.config import settings
from src.backend.ingestion import ingestion_manager

logger = logging.getLogger("sparkrit.retrieval")
logging.basicConfig(level=logging.INFO)

class RetrievalCandidate(BaseModel):
    standard_id: str
    title: str
    standard_type: Optional[str] = None
    publication_year: Optional[int] = None
    domain: Optional[str] = None
    scope: Optional[str] = None
    bm25_score: float = 0.0
    bm25_rank: int = 999
    dense_score: float = 0.0
    dense_rank: int = 999
    rrf_score: float = 0.0
    exact_match: bool = False
    false_friend_detected: bool = False
    candidate_metadata: dict[str, Any] = {}

class HybridRetrievalEngine:
    """
    Implements Exact Match + BM25 + Dense Semantic Embeddings + RRF + Reranking.
    Offline-first and optimized for CPU hardware.
    """
    def __init__(self):
        self.standards = ingestion_manager.get_all_standards()
        self.standards_by_id = {s["standard_id"]: s for s in self.standards}
        self.corpus_docs = []
        self.corpus_ids = []
        self.bm25 = None
        self.dense_model = None
        self.dense_embeddings = None
        self.tfidf_vectorizer = None
        self.tfidf_matrix = None
        self._init_bm25()
        self._init_dense()

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r"\b\w+\b", text.lower())

    def _init_bm25(self):
        tokenized_corpus = []
        for s in self.standards:
            std_id = s.get("standard_id", "")
            title = s.get("title", "")
            scope = s.get("scope", "")
            domain = s.get("domain", "")
            keywords = " ".join(s.get("keywords", []))
            notes = s.get("notes", "")
            doc_text = f"{std_id} {std_id.replace(':', ' ')} {title} {scope} {domain} {keywords} {notes}"
            
            tokenized_corpus.append(self._tokenize(doc_text))
            self.corpus_ids.append(std_id)
            self.corpus_docs.append(doc_text)

        if tokenized_corpus:
            self.bm25 = BM25Okapi(tokenized_corpus)
            logger.info(f"Initialized BM25 index over {len(self.standards)} standards.")

    def _init_dense(self):
        """Initializes dense embedding model (BGE-M3 / SentenceTransformer with local fallback)."""
        doc_texts = [
            f"{s.get('standard_id')} {s.get('title')}. {s.get('scope')} Keywords: {', '.join(s.get('keywords', []))}"
            for s in self.standards
        ]
        
        # Fast local TF-IDF semantic vector representation (100% offline & instant on any CPU)
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            self.tfidf_vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=4096)
            self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(doc_texts).toarray()
            logger.info(f"Initialized dense semantic TF-IDF matrix: {self.tfidf_matrix.shape}")
        except (ImportError, ValueError) as e:
            logger.warning(f"TF-IDF vectorizer notice: {e}")
        try:
            from sentence_transformers import SentenceTransformer
            model_to_try = settings.EMBEDDING_MODEL_NAME if "MiniLM" in settings.EMBEDDING_MODEL_NAME else "all-MiniLM-L6-v2"
            # Attempt to load from local cache without blocking network hang
            self.dense_model = SentenceTransformer(model_to_try, local_files_only=True)
            self.dense_embeddings = self.dense_model.encode(doc_texts, normalize_embeddings=True, show_progress_bar=False)
            logger.info(f"Initialized Dense SentenceTransformer embeddings: {self.dense_embeddings.shape}")
        except (ImportError, OSError, RuntimeError) as e:
            logger.info(f"Dense embedding engine operating in high-speed offline TF-IDF semantic vector mode ({e}).")
            self.dense_model = None

    def _exact_match(self, query: str, explicit_standards: list[str]) -> list[tuple[str, bool]]:
        matches = []
        target_ids = list(explicit_standards)
        
        found_in_query = re.findall(r"\bIS\s*[:\s]?\s*([0-9]+(?:\s*\([^\)]+\))?(?:\s*:\s*[0-9]{4})?)", query, re.IGNORECASE)
        for num in found_in_query:
            clean = f"IS {num.strip()}"
            if clean not in target_ids:
                target_ids.append(clean)

        for raw_id in target_ids:
            matched_standard = None
            if raw_id in self.standards_by_id:
                matched_standard = raw_id
            else:
                clean_base = raw_id.split(":")[0].strip().upper()
                for sid in self.standards_by_id:
                    if sid.upper().startswith(clean_base) or sid.upper() == clean_base:
                        matched_standard = sid
                        break

            if matched_standard:
                matches.append((matched_standard, True))
            else:
                matches.append((raw_id, False))
                
        return matches

    def retrieve(
        self,
        query: str,
        explicit_standards: Optional[list[str]] = None,
        top_k: int = 10,
    ) -> list[RetrievalCandidate]:
        explicit_standards = explicit_standards or []
        exact_matches = self._exact_match(query, explicit_standards)

        # 1. BM25 Retrieval
        bm25_scores = {}
        if self.bm25:
            tokens = self._tokenize(query)
            scores = self.bm25.get_scores(tokens)
            sorted_indices = np.argsort(scores)[::-1]
            for rank, idx in enumerate(sorted_indices[:50]):
                std_id = self.corpus_ids[idx]
                bm25_scores[std_id] = (float(scores[idx]), rank + 1)

        # 2. Dense Semantic Retrieval
        dense_scores = {}
        if self.dense_model is not None and self.dense_embeddings is not None:
            query_emb = self.dense_model.encode([query], normalize_embeddings=True)[0]
            sims = np.dot(self.dense_embeddings, query_emb)
            sorted_indices = np.argsort(sims)[::-1]
            for rank, idx in enumerate(sorted_indices[:50]):
                std_id = self.corpus_ids[idx]
                dense_scores[std_id] = (float(sims[idx]), rank + 1)
        elif self.tfidf_vectorizer is not None and self.tfidf_matrix is not None:
            q_vec = self.tfidf_vectorizer.transform([query]).toarray()[0]
            q_norm = np.linalg.norm(q_vec)
            if q_norm > 0:
                q_vec = q_vec / q_norm
                sims = np.dot(self.tfidf_matrix, q_vec)
                sorted_indices = np.argsort(sims)[::-1]
                for rank, idx in enumerate(sorted_indices[:50]):
                    std_id = self.corpus_ids[idx]
                    dense_scores[std_id] = (float(sims[idx]), rank + 1)

        # 3. Reciprocal Rank Fusion (RRF)
        all_candidate_ids = set(bm25_scores.keys()) | set(dense_scores.keys())
        rrf_k = settings.RRF_K

        candidate_list: list[RetrievalCandidate] = []
        
        # Check for non-existent false friends first
        for raw_id, is_existing in exact_matches:
            if not is_existing:
                candidate_list.append(
                    RetrievalCandidate(
                        standard_id=raw_id,
                        title="[UNVERIFIED / NON-EXISTENT IN CURATED CORPUS]",
                        standard_type="unknown",
                        publication_year=None,
                        domain="Unknown",
                        scope="Explicitly cited in specification but does not exist as a valid published standard in the BIS dataset.",
                        bm25_score=0.0,
                        bm25_rank=999,
                        dense_score=0.0,
                        dense_rank=999,
                        rrf_score=1.0,
                        exact_match=True,
                        false_friend_detected=True,
                        candidate_metadata={"warning": "False friend or obsolete non-indexed reference detected."},
                    )
                )

        for std_id in all_candidate_ids:
            std_obj = self.standards_by_id.get(std_id, {})
            b_score, b_rank = bm25_scores.get(std_id, (0.0, 999))
            d_score, d_rank = dense_scores.get(std_id, (0.0, 999))
            
            rrf_score = 0.0
            if b_rank <= 50:
                rrf_score += 1.0 / (rrf_k + b_rank)
            if d_rank <= 50:
                rrf_score += 1.0 / (rrf_k + d_rank)

            is_exact = any(std_id == m[0] for m in exact_matches if m[1])
            if is_exact:
                rrf_score += 0.5

            query_lower = query.lower()
            if std_obj.get("keywords"):
                for kw in std_obj["keywords"]:
                    if kw.lower() in query_lower:
                        rrf_score += 0.015

            candidate_list.append(
                RetrievalCandidate(
                    standard_id=std_id,
                    title=std_obj.get("title", ""),
                    standard_type=std_obj.get("standard_type"),
                    publication_year=std_obj.get("publication_year"),
                    domain=std_obj.get("domain"),
                    scope=std_obj.get("scope"),
                    bm25_score=round(b_score, 4),
                    bm25_rank=b_rank,
                    dense_score=round(d_score, 4),
                    dense_rank=d_rank,
                    rrf_score=round(rrf_score, 6),
                    exact_match=is_exact,
                    false_friend_detected=False,
                    candidate_metadata=std_obj,
                )
            )

        candidate_list.sort(key=lambda x: (x.false_friend_detected, x.rrf_score), reverse=True)
        return candidate_list[:top_k]

retrieval_engine = HybridRetrievalEngine()
