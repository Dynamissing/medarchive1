from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field
from rapidfuzz import fuzz
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import Settings, get_settings
from app.core.constants import MatchDecisionStatus
from app.db.models import MatchingCandidate, Service, ServiceSynonym
from app.services.admin.service_directory_import import normalize_text as normalize_catalog_text
from app.services.normalization.row_normalization import PriceItemPayload


@dataclass(frozen=True)
class MatchThresholdPolicy:
    auto_accept: float = 0.94
    needs_review: float = 0.72

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> MatchThresholdPolicy:
        resolved = settings or get_settings()
        return cls(
            auto_accept=resolved.match_auto_accept_threshold,
            needs_review=resolved.match_needs_review_threshold,
        )

    def classify(self, score: float) -> MatchDecisionStatus:
        if score >= self.auto_accept:
            return MatchDecisionStatus.AUTO_ACCEPT
        if score >= self.needs_review:
            return MatchDecisionStatus.NEEDS_REVIEW
        return MatchDecisionStatus.UNMATCHED


class MatchExplanation(BaseModel):
    methods: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    components: dict[str, float] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class MatchCandidateResult(BaseModel):
    service_id: UUID
    service_name: str
    service_code: str | None = None
    tariff_code: str | None = None
    score: float
    decision_status: MatchDecisionStatus
    strategy: str
    explanation: MatchExplanation


class MatchResult(BaseModel):
    row_hash: str
    normalized_query: str
    decision_status: MatchDecisionStatus
    candidates: list[MatchCandidateResult]
    warnings: list[str] = Field(default_factory=list)


@dataclass(frozen=True)
class ServiceIndexEntry:
    service: Service
    searchable_values: tuple[str, ...]


class LayeredMatchingEngine:
    def __init__(
        self,
        db: Session,
        settings: Settings | None = None,
        thresholds: MatchThresholdPolicy | None = None,
    ) -> None:
        self.db = db
        self.settings = settings or get_settings()
        self.thresholds = thresholds or MatchThresholdPolicy.from_settings(self.settings)
        self._llm_cache: dict[str, dict[str, Any]] = {}

    def match_row(
        self,
        row: PriceItemPayload,
        *,
        top_k: int = 5,
        persist_review: bool = True,
        price_document_id: UUID | None = None,
    ) -> MatchResult:
        normalized_query = normalize_query(row.normalized_service_name or row.service_name)
        row_hash = row_payload_hash(row)
        warnings: list[str] = []
        if not normalized_query:
            result = MatchResult(
                row_hash=row_hash,
                normalized_query="",
                decision_status=MatchDecisionStatus.UNMATCHED,
                candidates=[],
                warnings=["Row has no normalized service name."],
            )
            if persist_review:
                self.persist_candidates(result, row, price_document_id=price_document_id)
            return result

        entries = load_service_index(self.db)
        candidates = [score_entry(row, normalized_query, entry, self.thresholds) for entry in entries]
        candidates = [candidate for candidate in candidates if candidate.score > 0]
        candidates.sort(key=lambda candidate: candidate.score, reverse=True)
        candidates = candidates[:top_k]

        if self.settings.match_enable_embeddings:
            warnings.append("Sentence-transformers rerank is enabled but no local reranker is configured.")
        if self.settings.match_enable_openrouter:
            warnings.extend(self._maybe_openrouter_fallback(row, candidates))

        decision = candidates[0].decision_status if candidates else MatchDecisionStatus.UNMATCHED
        result = MatchResult(
            row_hash=row_hash,
            normalized_query=normalized_query,
            decision_status=decision,
            candidates=candidates,
            warnings=warnings,
        )
        if persist_review and decision != MatchDecisionStatus.AUTO_ACCEPT:
            self.persist_candidates(result, row, price_document_id=price_document_id)
        return result

    def persist_candidates(
        self,
        result: MatchResult,
        row: PriceItemPayload,
        *,
        price_document_id: UUID | None = None,
    ) -> list[MatchingCandidate]:
        self.db.execute(delete(MatchingCandidate).where(MatchingCandidate.row_hash == result.row_hash))
        stored: list[MatchingCandidate] = []
        row_payload = row.model_dump(mode="json")
        source_locator = dict(row.source_locator)
        if not result.candidates:
            stored_candidate = MatchingCandidate(
                row_hash=result.row_hash,
                price_document_id=price_document_id,
                service_id=None,
                rank=1,
                score=0.0,
                decision_status=MatchDecisionStatus.UNMATCHED.value,
                strategy="none",
                normalized_query=result.normalized_query,
                source_code=row.source_code,
                source_locator=source_locator,
                row_payload=row_payload,
                explanation={"warnings": result.warnings or ["No candidate reached the review threshold."]},
            )
            self.db.add(stored_candidate)
            stored.append(stored_candidate)
        else:
            for rank, candidate in enumerate(result.candidates, start=1):
                stored_candidate = MatchingCandidate(
                    row_hash=result.row_hash,
                    price_document_id=price_document_id,
                    service_id=candidate.service_id,
                    rank=rank,
                    score=candidate.score,
                    decision_status=candidate.decision_status.value,
                    strategy=candidate.strategy,
                    normalized_query=result.normalized_query,
                    source_code=row.source_code,
                    source_locator=source_locator,
                    row_payload=row_payload,
                    explanation=candidate.explanation.model_dump(mode="json"),
                )
                self.db.add(stored_candidate)
                stored.append(stored_candidate)
        self.db.commit()
        return stored

    def _maybe_openrouter_fallback(
        self,
        row: PriceItemPayload,
        candidates: list[MatchCandidateResult],
    ) -> list[str]:
        if candidates and candidates[0].score >= self.thresholds.needs_review:
            return []
        if not self.settings.openrouter_api_key:
            return ["OpenRouter fallback is enabled but OPENROUTER_API_KEY is not configured."]
        cache_key = hashlib.sha256(
            json.dumps(row.model_dump(mode="json"), ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()
        if cache_key in self._llm_cache:
            return []
        self._llm_cache[cache_key] = {"status": "skipped", "reason": "network fallback not invoked in baseline engine"}
        return ["OpenRouter fallback is configured but baseline matching did not invoke external LLM calls."]


def load_service_index(db: Session) -> list[ServiceIndexEntry]:
    services = db.scalars(select(Service).options(selectinload(Service.synonyms))).all()
    entries: list[ServiceIndexEntry] = []
    for service in services:
        values = {normalize_query(service.normalized_name), normalize_query(service.name_ru)}
        values.update(normalize_query(synonym.normalized_value) for synonym in service.synonyms)
        entries.append(ServiceIndexEntry(service=service, searchable_values=tuple(value for value in values if value)))
    return entries


def score_entry(
    row: PriceItemPayload,
    normalized_query: str,
    entry: ServiceIndexEntry,
    thresholds: MatchThresholdPolicy,
) -> MatchCandidateResult:
    service = entry.service
    explanation = MatchExplanation()
    score = 0.0
    strategy = "fuzzy"

    if normalize_query(service.normalized_name) == normalized_query:
        score = 1.0
        strategy = "exact_name"
        explanation.methods.append("exact_normalized_name")
        explanation.reasons.append("Normalized row name equals service normalized name.")
        explanation.components["exact_name"] = 1.0
    elif normalized_query in entry.searchable_values:
        score = 0.97
        strategy = "synonym"
        explanation.methods.append("synonym")
        explanation.reasons.append("Normalized row name equals a deterministic service synonym.")
        explanation.components["synonym"] = 0.97
    else:
        best_fuzzy = max((fuzz.WRatio(normalized_query, value) / 100 for value in entry.searchable_values), default=0.0)
        best_token = max((token_score(normalized_query, value) for value in entry.searchable_values), default=0.0)
        blended = (best_fuzzy * 0.65) + (best_token * 0.35)
        if blended >= 0.45:
            score = blended
            explanation.methods.extend(["rapidfuzz", "token_overlap"])
            explanation.reasons.append("Candidate selected by blended fuzzy and token-based similarity.")
            explanation.components["rapidfuzz"] = round(best_fuzzy, 4)
            explanation.components["token_overlap"] = round(best_token, 4)

    if row.source_code and service_code_matches(row.source_code, service):
        score = max(score, 0.74) + 0.08
        strategy = f"{strategy}_code_hint" if strategy else "code_hint"
        explanation.methods.append("source_code_hint")
        explanation.reasons.append("Source code matches service code or tariff code.")
        explanation.components["source_code_hint"] = 0.08

    score = min(round(score, 4), 1.0)
    decision = thresholds.classify(score)
    if decision == MatchDecisionStatus.AUTO_ACCEPT and strategy.startswith("fuzzy"):
        explanation.warnings.append("Auto-accept comes from similarity scoring; review threshold tuning is recommended.")
    return MatchCandidateResult(
        service_id=service.id,
        service_name=service.name_ru,
        service_code=service.code,
        tariff_code=service.tariff_code,
        score=score,
        decision_status=decision,
        strategy=strategy,
        explanation=explanation,
    )


def service_code_matches(source_code: str, service: Service) -> bool:
    normalized = normalize_code(source_code)
    return normalized in {normalize_code(service.code), normalize_code(service.tariff_code)}


def token_score(left: str, right: str) -> float:
    left_tokens = set(left.split())
    right_tokens = set(right.split())
    if not left_tokens or not right_tokens:
        return 0.0
    intersection = len(left_tokens & right_tokens)
    union = len(left_tokens | right_tokens)
    return intersection / union


def normalize_query(value: str | None) -> str:
    return normalize_catalog_text(value or "")


def normalize_code(value: str | None) -> str:
    return "".join((value or "").casefold().split())


def row_payload_hash(row: PriceItemPayload) -> str:
    payload = row.model_dump(mode="json")
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
