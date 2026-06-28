from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import MatchDecisionStatus
from app.db.base import Base, TimestampMixin


class MatchingCandidate(TimestampMixin, Base):
    __tablename__ = "matching_candidates"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    row_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    price_document_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("price_documents.id", ondelete="SET NULL"),
        index=True,
    )
    service_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("services.id", ondelete="SET NULL"),
        index=True,
    )
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    decision_status: Mapped[str] = mapped_column(
        String(32),
        default=MatchDecisionStatus.UNMATCHED.value,
        nullable=False,
        index=True,
    )
    strategy: Mapped[str] = mapped_column(String(64), nullable=False)
    normalized_query: Mapped[str] = mapped_column(Text, nullable=False)
    source_code: Mapped[str | None] = mapped_column(String(255), index=True)
    source_locator: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    row_payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    explanation: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    service: Mapped["Service | None"] = relationship()
