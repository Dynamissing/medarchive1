from __future__ import annotations

import json
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.config import Settings, get_settings
from app.core.constants import AnomalySeverity
from app.services.normalization.row_normalization import PriceItemAmountPayload, PriceItemPayload


class ValidationIssue(BaseModel):
    code: str
    severity: AnomalySeverity
    message: str
    payload: dict[str, Any] = Field(default_factory=dict)
    action_type: str | None = None


class CurrencyConversionResult(BaseModel):
    original_amount: Decimal
    original_currency: str
    amount_kzt: Decimal | None = None
    warnings: list[ValidationIssue] = Field(default_factory=list)


class LocalCurrencyConversionProvider:
    def __init__(self, rates_to_kzt: dict[str, Decimal] | None = None) -> None:
        self.rates_to_kzt = {code.upper(): rate for code, rate in (rates_to_kzt or {}).items()}
        self.rates_to_kzt.setdefault("KZT", Decimal("1"))

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> LocalCurrencyConversionProvider:
        resolved = settings or get_settings()
        try:
            raw_rates = json.loads(resolved.currency_conversion_rates or "{}")
        except json.JSONDecodeError:
            raw_rates = {}
        rates: dict[str, Decimal] = {}
        for code, value in raw_rates.items():
            try:
                rates[str(code).upper()] = Decimal(str(value))
            except (InvalidOperation, ValueError):
                continue
        return cls(rates)

    def convert_to_kzt(self, amount: Decimal, currency: str | None) -> CurrencyConversionResult:
        normalized_currency = (currency or "KZT").upper()
        rate = self.rates_to_kzt.get(normalized_currency)
        if rate is None:
            return CurrencyConversionResult(
                original_amount=amount,
                original_currency=normalized_currency,
                warnings=[
                    ValidationIssue(
                        code="non_kzt_preserved",
                        severity=AnomalySeverity.WARNING,
                        message=f"No local conversion rate configured for {normalized_currency}; original amount preserved.",
                        payload={"currency": normalized_currency, "amount": str(amount)},
                        action_type="configure_currency_rate",
                    )
                ],
            )
        return CurrencyConversionResult(
            original_amount=amount,
            original_currency=normalized_currency,
            amount_kzt=(amount * rate).quantize(Decimal("0.01")),
        )


def validate_price_row(
    row: PriceItemPayload,
    *,
    today: date | None = None,
    conversion_provider: LocalCurrencyConversionProvider | None = None,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    check_date = today or date.today()
    provider = conversion_provider or LocalCurrencyConversionProvider.from_settings()

    if not row.normalized_service_name.strip():
        issues.append(
            ValidationIssue(
                code="empty_service_name",
                severity=AnomalySeverity.ERROR,
                message="Service name is empty after normalization.",
                action_type="review_service_name",
            )
        )

    if not row.amounts:
        issues.append(
            ValidationIssue(
                code="no_recognizable_data",
                severity=AnomalySeverity.ERROR,
                message="Row has no recognizable price data.",
                action_type="review_document_extraction",
            )
        )

    if row.effective_date and row.effective_date > check_date:
        issues.append(
            ValidationIssue(
                code="future_effective_date",
                severity=AnomalySeverity.WARNING,
                message="Effective date is in the future.",
                payload={"effective_date": row.effective_date.isoformat(), "today": check_date.isoformat()},
                action_type="verify_effective_date",
            )
        )

    amounts_by_label = {normalize_amount_label(amount.label): amount for amount in row.amounts}
    resident = first_labeled_amount(amounts_by_label, ("resident", "резидент"))
    nonresident = first_labeled_amount(amounts_by_label, ("nonresident", "non resident", "нерезидент"))
    if resident and nonresident and nonresident.amount < resident.amount:
        issues.append(
            ValidationIssue(
                code="nonresident_less_than_resident",
                severity=AnomalySeverity.WARNING,
                message="Nonresident price is lower than resident price.",
                payload={"resident": str(resident.amount), "nonresident": str(nonresident.amount)},
                action_type="verify_price_tiers",
            )
        )

    for amount in row.amounts:
        if amount.amount <= 0:
            issues.append(
                ValidationIssue(
                    code="non_positive_price",
                    severity=AnomalySeverity.ERROR,
                    message="Price must be a positive numeric value.",
                    payload={"label": amount.label, "amount": str(amount.amount)},
                    action_type="correct_price",
                )
            )
        conversion = provider.convert_to_kzt(amount.amount, amount.currency)
        issues.extend(conversion.warnings)

    return issues


def validate_document_rows(rows: list[PriceItemPayload]) -> list[ValidationIssue]:
    if rows:
        return []
    return [
        ValidationIssue(
            code="no_recognizable_data_document",
            severity=AnomalySeverity.ERROR,
            message="Document produced no recognizable normalized price rows.",
            action_type="review_document_extraction",
        )
    ]


def normalize_amount_label(label: str | None) -> str:
    return " ".join((label or "").casefold().replace("_", " ").replace("-", " ").split())


def first_labeled_amount(
    amounts_by_label: dict[str, PriceItemAmountPayload],
    labels: tuple[str, ...],
) -> PriceItemAmountPayload | None:
    for label, amount in amounts_by_label.items():
        if any(expected in label for expected in labels):
            return amount
    return None


def duplicate_key(
    row: PriceItemPayload,
    *,
    service_id: UUID | None = None,
    amount: PriceItemAmountPayload | None = None,
) -> tuple[str | None, str, str | None, date | None, str | None]:
    service_key = str(service_id) if service_id else row.normalized_service_name
    amount_label = normalize_amount_label(amount.label) if amount else None
    return (row.partner_name, service_key, amount_label, row.effective_date, row.source_code)
