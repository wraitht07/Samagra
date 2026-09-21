import json
import logging
from typing import Optional

import httpx
from pydantic import BaseModel

from src.backend.config import settings
from src.backend.extraction import ExtractedClause
from src.backend.verification import ClauseVerificationResult

logger = logging.getLogger("sparkrit.reasoning")

class LLMReasoningOutput(BaseModel):
    ai_invoked: bool = False
    ai_status_label: str = "AI NOT INVOKED"
    escalation_reason: Optional[str] = None
    resolved_standard_id: Optional[str] = None
    reasoning_explanation: Optional[str] = None
    human_review_required: bool = False

SYSTEM_PROMPT = """You are the Samagra Reasoning Engine for Indian Standards (BIS).
Rules:
1. Reason ONLY over the provided candidate standards and verified evidence.
2. NEVER invent standard numbers, versions, amendments, or regulations.
3. If evidence is insufficient, state 'HUMAN REVIEW REQUIRED'.
4. Provide clear, factual justifications."""

class LocalLLMReasoningEngine:
    """
    Escalation layer: executes strictly grounded reasoning over retrieved evidence
    only when semantic ambiguity is detected.
    """

    def __init__(self):
        self.api_base = getattr(settings, "LLM_API_BASE", None)
        self.model_name = getattr(settings, "LLM_MODEL", None)

    async def resolve_ambiguity(
        self,
        clause: ExtractedClause,
        verification_result: ClauseVerificationResult,
    ) -> LLMReasoningOutput:
        # Check if AI invocation is needed
        if not verification_result.ambiguity_detected:
            if verification_result.requires_human_review or verification_result.insufficient_evidence:
                return LLMReasoningOutput(
                    ai_invoked=False,
                    ai_status_label="AI NOT INVOKED — HUMAN REVIEW REQUIRED",
                    escalation_reason="Insufficient evidence in curated corpus.",
                    resolved_standard_id=None,
                    reasoning_explanation="Deterministic verification found insufficient evidence. Human review required.",
                    human_review_required=True,
                )
            else:
                top_std = verification_result.recommended_standard
                return LLMReasoningOutput(
                    ai_invoked=False,
                    ai_status_label="AI NOT INVOKED",
                    escalation_reason=None,
                    resolved_standard_id=top_std.standard_id if top_std else None,
                    reasoning_explanation="Deterministic retrieval and verification succeeded without ambiguity.",
                    human_review_required=False,
                )

        # Ambiguity detected: escalate to Local LLM
        candidates = [verification_result.recommended_standard] + verification_result.alternative_candidates
        candidates = [c for c in candidates if c is not None]

        evidence_context = []
        for idx, c in enumerate(candidates[:4]):
            evidence_context.append({
                "candidate_index": idx + 1,
                "standard_id": c.standard_id,
                "title": c.title,
                "scope": c.raw_metadata.get("scope", ""),
                "notes": c.raw_metadata.get("notes", ""),
                "certification": c.certification_scheme,
            })

        user_prompt = f"""Requirement Clause:
"{clause.cleaned_requirement}"

Candidate Evidence:
{json.dumps(evidence_context, indent=2)}

Ambiguity Flag:
{verification_result.ambiguity_reason}

TASK:
Analyze the clause against ONLY the candidate evidence above. Which standard applies and why?
If evidence is insufficient, state 'HUMAN REVIEW REQUIRED'."""

        # Attempt LLM call if API is configured
        if self.api_base and self.model_name:
            try:
                async with httpx.AsyncClient(timeout=4.0) as client:
                    res = await client.post(
                        f"{self.api_base}/chat/completions",
                        json={
                            "model": self.model_name,
                            "messages": [
                                {"role": "system", "content": SYSTEM_PROMPT},
                                {"role": "user", "content": user_prompt}
                            ],
                            "temperature": 0.0,
                            "max_tokens": 250,
                        }
                    )
                    if res.status_code == 200:
                        resp_json = res.json()
                        content = resp_json["choices"][0]["message"]["content"]

                        resolved_id = None
                        for c in candidates:
                            if c.standard_id in content:
                                resolved_id = c.standard_id
                                break

                        return LLMReasoningOutput(
                            ai_invoked=True,
                            ai_status_label="LOCAL LLM INVOKED",
                            escalation_reason=verification_result.ambiguity_reason,
                            resolved_standard_id=resolved_id or candidates[0].standard_id,
                            reasoning_explanation=content.strip(),
                            human_review_required="HUMAN REVIEW" in content.upper(),
                        )
            except (httpx.HTTPError, httpx.ConnectError, httpx.TimeoutException) as e:
                logger.info(f"Local LLM service not reachable ({e}). Falling back to deterministic resolution.")

        # Fallback: Deterministic resolution without LLM
        selected = candidates[0]
        return LLMReasoningOutput(
            ai_invoked=True,
            ai_status_label="LOCAL LLM INVOKED (FALLBACK)",
            escalation_reason=verification_result.ambiguity_reason,
            resolved_standard_id=selected.standard_id,
            reasoning_explanation=f"Fallback: Selected {selected.standard_id} based on highest retrieval score.",
            human_review_required=False,
        )

reasoning_engine = LocalLLMReasoningEngine()