from __future__ import annotations

import hashlib
from collections import defaultdict
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.models import PriceDocument, PriceItemVersion, Service, ServiceSynonym
from app.services.admin.service_directory_import import generate_synonyms, normalize_text
from app.services.normalization.row_normalization import PriceItemPayload

logger = get_logger(__name__)


def publish_parsed_services(
    db: Session,
    document: PriceDocument,
    rows: list[PriceItemPayload],
    price_versions: list[PriceItemVersion],
) -> dict:
    """Bridge parsed rows into the Service table so they become searchable.

    For each unique normalized_service_name in the parsed rows, finds an existing
    Service or creates a new one. Then links all PriceItemVersion records to the
    corresponding Service by setting service_id.

    Returns a summary dict with created/linked/skipped counts.
    """
    source_filename = document.file_asset.original_filename if document.file_asset else None
    document_id = str(document.id)

    row_index_by_name: dict[str, list[int]] = defaultdict(list)
    for idx, row in enumerate(rows):
        key = normalize_text(row.normalized_service_name)
        if key:
            row_index_by_name[key].append(idx)

    version_index_by_name: dict[str, list[int]] = defaultdict(list)
    for idx, version in enumerate(price_versions):
        key = normalize_text(version.normalized_service_name)
        if key:
            version_index_by_name[key].append(idx)

    all_names = set(row_index_by_name.keys()) | set(version_index_by_name.keys())

    created = 0
    linked = 0
    skipped = 0

    for name_key in all_names:
        service = db.scalar(select(Service).where(Service.normalized_name == name_key))
        if service is None:
            source_hash = _make_source_hash(name_key, document_id)
            service = Service(
                import_batch=document_id,
                source_type="parsed_document",
                source_hash=source_hash,
                name_ru=_find_original_name(rows, price_versions, name_key),
                normalized_name=name_key,
                warnings=[],
                raw_data={"source_document_id": document_id, "source_filename": source_filename},
            )
            db.add(service)
            db.flush()
            created += 1
            _create_synonyms(db, service, name_key, source_filename)

        for idx in version_index_by_name.get(name_key, []):
            version = price_versions[idx]
            if version.service_id is None:
                version.service_id = service.id
                linked += 1
            elif version.service_id != service.id:
                pass

    db.flush()

    return {
        "published_services_created": created,
        "published_services_linked": linked,
        "published_services_skipped": skipped,
        "published_services_total": len(all_names),
    }


def _make_source_hash(normalized_name: str, document_id: str) -> str:
    payload = f"{normalized_name}:{document_id}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def _find_original_name(
    rows: list[PriceItemPayload],
    price_versions: list[PriceItemVersion],
    normalized_name: str,
) -> str:
    for row in rows:
        if normalize_text(row.normalized_service_name) == normalized_name:
            return row.service_name
    for version in price_versions:
        if normalize_text(version.normalized_service_name) == normalized_name:
            return version.service_name
    return normalized_name


def _create_synonyms(
    db: Session,
    service: Service,
    normalized_name: str,
    source_filename: str | None,
) -> None:
    existing_values = {
        syn.normalized_value
        for syn in db.scalars(
            select(ServiceSynonym).where(ServiceSynonym.service_id == service.id)
        ).all()
    }
    for synonym_value in generate_synonyms(service.name_ru):
        syn_normalized = normalize_text(synonym_value)
        if syn_normalized and syn_normalized not in existing_values:
            db.add(
                ServiceSynonym(
                    service_id=service.id,
                    value=synonym_value,
                    normalized_value=syn_normalized,
                    source="parsed_document",
                )
            )
            existing_values.add(syn_normalized)
