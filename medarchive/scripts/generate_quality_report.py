"""Print aggregate MedArchive quality metrics as JSON."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from sqlalchemy import func, select

from app.core.logging import configure_logging
from app.db.models import AnomalyFlag, MatchingCandidate, PriceDocument, PriceItemVersion
from app.db.session import SessionLocal


def main() -> None:
    configure_logging()
    with SessionLocal() as db:
        report = {
            "generated_at": datetime.now(UTC).isoformat(),
            "parsing": dict(db.execute(select(PriceDocument.status, func.count(PriceDocument.id)).group_by(PriceDocument.status)).all()),
            "matching": dict(
                db.execute(select(MatchingCandidate.decision_status, func.count(MatchingCandidate.id)).group_by(MatchingCandidate.decision_status)).all()
            ),
            "validation": dict(db.execute(select(AnomalyFlag.code, func.count(AnomalyFlag.id)).group_by(AnomalyFlag.code)).all()),
            "price_history": {
                "active": int(db.scalar(select(func.count(PriceItemVersion.id)).where(PriceItemVersion.is_active.is_(True))) or 0),
                "inactive": int(db.scalar(select(func.count(PriceItemVersion.id)).where(PriceItemVersion.is_active.is_(False))) or 0),
            },
        }

    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
