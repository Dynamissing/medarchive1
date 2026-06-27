from __future__ import annotations

from enum import StrEnum


class ProcessingStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class ReviewStatus(StrEnum):
    UNREVIEWED = "unreviewed"
    APPROVED = "approved"
    REJECTED = "rejected"


class ImportBatchStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class FileAssetKind(StrEnum):
    ORIGINAL_ARCHIVE = "original_archive"
    ARCHIVE_MEMBER = "archive_member"


class PriceDocumentStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    PARSED = "parsed"
    FAILED = "failed"


class MatchDecisionStatus(StrEnum):
    AUTO_ACCEPT = "auto_accept"
    NEEDS_REVIEW = "needs_review"
    UNMATCHED = "unmatched"


class PriceItemVersionStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class AnomalySeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class VerificationActionStatus(StrEnum):
    OPEN = "open"
    COMPLETED = "completed"
    DISMISSED = "dismissed"
