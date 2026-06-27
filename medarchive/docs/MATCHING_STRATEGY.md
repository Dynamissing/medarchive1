# Matching Strategy

## Goal

Describe how parsed archive records may later be matched to partner services or operational categories.

## Bootstrap Notes

- Layered backend matching is implemented as a service module.
- Service synonyms are generated during service-directory import using deterministic text rules only.
- Parsed rows can now be normalized into price-item-ready payloads before any matching is attempted.
- Early matching should be explainable and testable.
- Rules, scores, and model-assisted suggestions should be separable so quality can be measured.

## Candidate Inputs

- Normalized document metadata.
- Deterministically normalized row payloads with service names, source codes, amount variants, partner/date hints, and source locators.
- Service catalog entries and deterministic service synonyms.
- Partner constraints.
- Manual review feedback.
- Existing price item versions for duplicate and price-change checks after matching.

## Implemented Matching Layers

- Exact normalized service-name match.
- Deterministic synonym match.
- Optional source-code and tariff-code hint scoring.
- RapidFuzz string similarity.
- Token-overlap scoring.
- Configurable thresholds for `auto_accept`, `needs_review`, and `unmatched`.
- Persistence of review/unmatched candidates in `matching_candidates`.

## Explanation Payloads

Each candidate records:

- Matching methods used.
- Human-readable reasons.
- Score components.
- Warnings when a result is heuristic or optional paths are disabled.

## Optional Rerank And Fallback

- Sentence-transformers rerank is behind `MATCH_ENABLE_EMBEDDINGS` and disabled by default.
- OpenRouter fallback is behind `MATCH_ENABLE_OPENROUTER` and disabled by default.
- The baseline matcher does not require external model dependencies or network calls.
- Optional LLM fallback state is cached by row payload hash when configured.

## Threshold Policy

- `MATCH_AUTO_ACCEPT_THRESHOLD` defaults to `0.94`.
- `MATCH_NEEDS_REVIEW_THRESHOLD` defaults to `0.72`.
- Matches below the review threshold are treated as `unmatched`.
- Code hints can lift a weak text match into review, but do not auto-accept by themselves.

## Post-Match Validation

- Validation and history logic can persist active/inactive price versions once a normalized row has an accepted or reviewable service context.
- Duplicate detection uses partner, service or normalized name, amount label, effective date, and source code.
- Prior price versions are superseded, not overwritten.
- Anomaly flags and verification actions capture validation failures and review work.

## Open Questions

- What confidence thresholds are acceptable for demo use?
- Which matches require human approval?
- How should unmatched records be surfaced?
