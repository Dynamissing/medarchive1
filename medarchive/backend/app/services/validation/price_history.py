from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.core.constants import (
    AnomalySeverity,
    PriceItemVersionStatus,
    VerificationActionStatus,
)
from app.db.models import AnomalyFlag, PriceItemVersion, VerificationAction
from app.services.matching.engine import row_payload_hash
from app.services.normalization.row_normalization import PriceItemAmountPayload, PriceItemPayload
from app.services.validation.rules import (
    LocalCurrencyConversionProvider,
    ValidationIssue,
    duplicate_key,
    normalize_amount_label,
    validate_document_rows,
    validate_price_row,
)


PRICE_CHANGE_THRESHOLD = Decimal("0.50")


class PriceHistoryService:
    def __init__(
        self,
        db: Session,
        *,
        conversion_provider: LocalCurrencyConversionProvider | None = None,
        today: date | None = None,
    ) -> None:
        self.db = db
        self.conversion_provider = conversion_provider or LocalCurrencyConversionProvider.from_settings()
        self.today = today

    def validate_and_record(
        self,
        row: PriceItemPayload,
        *,
        service_id: UUID | None = None,
        price_document_id: UUID | None = None,
    ) -> list[PriceItemVersion]:
        issues = validate_price_row(row, today=self.today, conversion_provider=self.conversion_provider)
        row_hash = row_payload_hash(row)
        for issue in issues:
            self.persist_issue(issue, subject_type="price_row", row_hash=row_hash, payload=row.model_dump(mode="json"))

        if not row.amounts or not row.normalized_service_name.strip():
            self.db.commit()
            return []

        versions: list[PriceItemVersion] = []
        for amount in row.amounts:
            versions.append(
                self.record_amount(
                    row,
                    amount,
                    service_id=service_id,
                    price_document_id=price_document_id,
                )
            )
        self.db.commit()
        return versions

    def record_amount(
        self,
        row: PriceItemPayload,
        amount: PriceItemAmountPayload,
        *,
        service_id: UUID | None = None,
        price_document_id: UUID | None = None,
    ) -> PriceItemVersion:
        row_hash = row_payload_hash(row)
        active = self.find_active_version(row, amount, service_id=service_id)
        conversion = self.conversion_provider.convert_to_kzt(amount.amount, amount.currency)
        for issue in conversion.warnings:
            self.persist_issue(issue, subject_type="price_row", row_hash=row_hash, payload=row.model_dump(mode="json"))

        if active and active.amount == amount.amount and active.currency == (amount.currency or "KZT").upper():
            self.persist_issue(
                ValidationIssue(
                    code="duplicate_same_partner_service_date",
                    severity=AnomalySeverity.WARNING,
                    message="Duplicate partner/service/date price row detected.",
                    payload={"existing_version_id": str(active.id), "amount": str(amount.amount)},
                    action_type="review_duplicate",
                ),
                subject_type="price_item_version",
                subject_id=str(active.id),
                row_hash=row_hash,
            )
            return active

        new_version = PriceItemVersion(
            row_hash=row_hash,
            partner_name=row.partner_name,
            service_id=service_id,
            price_document_id=price_document_id,
            service_name=row.service_name,
            normalized_service_name=row.normalized_service_name,
            source_code=row.source_code,
            effective_date=row.effective_date,
            amount=amount.amount,
            currency=(amount.currency or "KZT").upper(),
            amount_kzt=conversion.amount_kzt,
            amount_label=normalize_amount_label(amount.label),
            status=PriceItemVersionStatus.ACTIVE.value,
            is_active=True,
            previous_version_id=active.id if active else None,
            source_locator=row.source_locator,
            raw_payload=row.model_dump(mode="json"),
        )
        self.db.add(new_version)
        self.db.flush()

        if active:
            active.is_active = False
            active.status = PriceItemVersionStatus.INACTIVE.value
            active.superseded_by_id = new_version.id
            active.supersede_reason = "new_price_version"
            self.flag_large_price_change(active, new_version, row_hash)
        return new_version

    def find_active_version(
        self,
        row: PriceItemPayload,
        amount: PriceItemAmountPayload,
        *,
        service_id: UUID | None,
    ) -> PriceItemVersion | None:
        partner_name, service_key, amount_label, effective_date, source_code = duplicate_key(
            row,
            service_id=service_id,
            amount=amount,
        )
        conditions = [
            PriceItemVersion.is_active.is_(True),
            PriceItemVersion.partner_name.is_(partner_name) if partner_name is None else PriceItemVersion.partner_name == partner_name,
            PriceItemVersion.effective_date.is_(effective_date) if effective_date is None else PriceItemVersion.effective_date == effective_date,
            PriceItemVersion.source_code.is_(source_code) if source_code is None else PriceItemVersion.source_code == source_code,
            PriceItemVersion.amount_label.is_(amount_label) if amount_label is None else PriceItemVersion.amount_label == amount_label,
        ]
        if service_id:
            conditions.append(PriceItemVersion.service_id == service_id)
        else:
            conditions.append(PriceItemVersion.normalized_service_name == service_key)
        return self.db.scalars(select(PriceItemVersion).where(and_(*conditions))).first()

    def flag_large_price_change(
        self,
        old_version: PriceItemVersion,
        new_version: PriceItemVersion,
        row_hash: str,
    ) -> None:
        if old_version.amount <= 0:
            return
        change_ratio = abs(Decimal(new_version.amount) - Decimal(old_version.amount)) / Decimal(old_version.amount)
        if change_ratio > PRICE_CHANGE_THRESHOLD:
            self.persist_issue(
                ValidationIssue(
                    code="price_change_gt_50_percent",
                    severity=AnomalySeverity.WARNING,
                    message="Price changed by more than 50 percent from the active version.",
                    payload={
                        "old_version_id": str(old_version.id),
                        "new_version_id": str(new_version.id),
                        "old_amount": str(old_version.amount),
                        "new_amount": str(new_version.amount),
                        "change_ratio": str(change_ratio.quantize(Decimal("0.0001"))),
                    },
                    action_type="review_large_price_change",
                ),
                subject_type="price_item_version",
                subject_id=str(new_version.id),
                row_hash=row_hash,
            )

    def persist_document_issue(self, rows: list[PriceItemPayload], *, payload: dict[str, Any] | None = None) -> None:
        for issue in validate_document_rows(rows):
            self.persist_issue(issue, subject_type="price_document", payload=payload or {})
        self.db.commit()

    def persist_issue(
        self,
        issue: ValidationIssue,
        *,
        subject_type: str,
        subject_id: str | None = None,
        row_hash: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> AnomalyFlag:
        merged_payload = dict(payload or {})
        merged_payload.update(issue.payload)
        flag = AnomalyFlag(
            subject_type=subject_type,
            subject_id=subject_id,
            row_hash=row_hash,
            code=issue.code,
            severity=issue.severity.value,
            message=issue.message,
            payload=merged_payload,
            resolved=False,
        )
        self.db.add(flag)
        self.db.flush()
        if issue.action_type:
            self.db.add(
                VerificationAction(
                    anomaly_flag_id=flag.id,
                    action_type=issue.action_type,
                    status=VerificationActionStatus.OPEN.value,
                    payload={"anomaly_code": issue.code},
                )
            )
        return flag
