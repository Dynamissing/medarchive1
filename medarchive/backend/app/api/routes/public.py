from __future__ import annotations

import hashlib
import re
from datetime import date
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import Select, distinct, func, or_, select
from sqlalchemy.orm import Session

from app.core.constants import PriceItemVersionStatus
from app.db.models import PriceItemVersion, Service, ServiceSynonym
from app.db.session import get_db

router = APIRouter(tags=["public"])

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


class SortDirection(StrEnum):
    ASC = "asc"
    DESC = "desc"


class ServiceSort(StrEnum):
    NAME = "name"
    CODE = "code"
    CATEGORY = "category"
    CREATED_AT = "created_at"


class PartnerSort(StrEnum):
    NAME = "name"
    SERVICES = "services"


class SearchType(StrEnum):
    SERVICE = "service"
    PARTNER = "partner"


class PageMeta(BaseModel):
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=MAX_PAGE_SIZE)
    total: int = Field(ge=0)
    pages: int = Field(ge=0)


class ServiceSummary(BaseModel):
    id: UUID
    name: str
    normalized_name: str
    code: str | None = None
    tariff_code: str | None = None
    category: str | None = None
    specialty: str | None = None


class ServiceListResponse(BaseModel):
    items: list[ServiceSummary]
    meta: PageMeta


class PartnerSummary(BaseModel):
    id: str
    name: str
    service_count: int = 0
    active_price_count: int = 0


class PartnerListResponse(BaseModel):
    items: list[PartnerSummary]
    meta: PageMeta


class PartnerServiceSummary(BaseModel):
    service: ServiceSummary
    partner: PartnerSummary
    latest_amount: Decimal | None = None
    currency: str | None = None
    effective_date: date | None = None


class PartnerServiceListResponse(BaseModel):
    items: list[PartnerServiceSummary]
    meta: PageMeta


class SearchResult(BaseModel):
    type: SearchType
    id: str
    label: str
    score: float
    payload: dict


class SearchResponse(BaseModel):
    items: list[SearchResult]
    meta: PageMeta


@router.get("/services", response_model=ServiceListResponse)
def list_services(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    q: str | None = Query(None, description="Search service names, codes, categories, and synonyms."),
    category: str | None = None,
    specialty: str | None = None,
    sort: ServiceSort = ServiceSort.NAME,
    direction: SortDirection = SortDirection.ASC,
) -> ServiceListResponse:
    query = select(Service)
    if q:
        query = apply_service_search(query, q)
    if category:
        query = query.where(Service.category == category)
    if specialty:
        query = query.where(Service.normalized_specialty.ilike(f"%{specialty.casefold()}%"))
    total = count_for(db, query)
    query = apply_service_sort(query, sort, direction)
    services = db.scalars(paginate(query, page, page_size)).all()
    return ServiceListResponse(items=[service_summary(service) for service in services], meta=page_meta(page, page_size, total))


@router.get("/services/{service_id}/partners", response_model=PartnerListResponse)
def list_service_partners(
    service_id: UUID,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    sort: PartnerSort = PartnerSort.NAME,
    direction: SortDirection = SortDirection.ASC,
) -> PartnerListResponse:
    if db.get(Service, service_id) is None:
        raise HTTPException(status_code=404, detail="Service not found")
    rows_query = partner_rows_query().where(PriceItemVersion.service_id == service_id)
    rows = db.execute(rows_query).all()
    partners = sorted(
        [partner_summary(row.partner_name, row.service_count, row.active_price_count) for row in rows],
        key=partner_sort_key(sort),
        reverse=direction == SortDirection.DESC,
    )
    total = len(partners)
    return PartnerListResponse(items=slice_items(partners, page, page_size), meta=page_meta(page, page_size, total))


@router.get("/partners", response_model=PartnerListResponse)
def list_partners(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    q: str | None = Query(None, description="Search partner names."),
    sort: PartnerSort = PartnerSort.NAME,
    direction: SortDirection = SortDirection.ASC,
) -> PartnerListResponse:
    rows_query = partner_rows_query()
    if q:
        rows_query = rows_query.where(PriceItemVersion.partner_name.ilike(f"%{q}%"))
    rows = db.execute(rows_query).all()
    partners = sorted(
        [partner_summary(row.partner_name, row.service_count, row.active_price_count) for row in rows],
        key=partner_sort_key(sort),
        reverse=direction == SortDirection.DESC,
    )
    total = len(partners)
    return PartnerListResponse(items=slice_items(partners, page, page_size), meta=page_meta(page, page_size, total))


@router.get("/partners/{partner_id}/services", response_model=PartnerServiceListResponse)
def list_partner_services(
    partner_id: str,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    sort: ServiceSort = ServiceSort.NAME,
    direction: SortDirection = SortDirection.ASC,
) -> PartnerServiceListResponse:
    partner_name = resolve_partner_name(db, partner_id)
    if partner_name is None:
        raise HTTPException(status_code=404, detail="Partner not found")
    query = (
        select(PriceItemVersion, Service)
        .join(Service, Service.id == PriceItemVersion.service_id, isouter=True)
        .where(
            PriceItemVersion.is_active.is_(True),
            PriceItemVersion.partner_name == partner_name,
        )
    )
    rows = db.execute(query).all()
    items = [partner_service_summary(version, service, partner_name) for version, service in rows]
    items.sort(key=partner_service_sort_key(sort), reverse=direction == SortDirection.DESC)
    total = len(items)
    return PartnerServiceListResponse(items=slice_items(items, page, page_size), meta=page_meta(page, page_size, total))


@router.get("/search", response_model=SearchResponse)
def search(
    q: str = Query(..., min_length=1, description="Search text across service and partner read models."),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    type: SearchType | None = Query(None, description="Limit search to services or partners."),
) -> SearchResponse:
    results: list[SearchResult] = []
    if type in (None, SearchType.SERVICE):
        service_query = apply_service_search(select(Service), q)
        for service in db.scalars(service_query.limit(MAX_PAGE_SIZE)).all():
            results.append(
                SearchResult(
                    type=SearchType.SERVICE,
                    id=str(service.id),
                    label=service.name_ru,
                    score=score_text(q, service.name_ru, service.code, service.category),
                    payload={**service_summary(service).model_dump(mode="json"), **service_price_payload(db, service.id)},
                )
            )
    if type in (None, SearchType.PARTNER):
        rows = db.execute(partner_rows_query().where(PriceItemVersion.partner_name.ilike(f"%{q}%"))).all()
        for row in rows:
            partner = partner_summary(row.partner_name, row.service_count, row.active_price_count)
            results.append(
                SearchResult(
                    type=SearchType.PARTNER,
                    id=partner.id,
                    label=partner.name,
                    score=score_text(q, partner.name),
                    payload=partner.model_dump(mode="json"),
                )
            )
    results.sort(key=lambda item: (item.score, item.label.casefold()), reverse=True)
    total = len(results)
    return SearchResponse(items=slice_items(results, page, page_size), meta=page_meta(page, page_size, total))


def apply_service_search(query: Select, search_text: str) -> Select:
    pattern = f"%{search_text}%"
    synonym_service_ids = select(ServiceSynonym.service_id).where(
        or_(ServiceSynonym.value.ilike(pattern), ServiceSynonym.normalized_value.ilike(pattern))
    )
    return query.where(
        or_(
            Service.name_ru.ilike(pattern),
            Service.normalized_name.ilike(pattern),
            Service.code.ilike(pattern),
            Service.tariff_code.ilike(pattern),
            Service.category.ilike(pattern),
            Service.normalized_specialty.ilike(pattern),
            Service.id.in_(synonym_service_ids),
        )
    )


def apply_service_sort(query: Select, sort: ServiceSort, direction: SortDirection) -> Select:
    columns = {
        ServiceSort.NAME: Service.normalized_name,
        ServiceSort.CODE: Service.code,
        ServiceSort.CATEGORY: Service.category,
        ServiceSort.CREATED_AT: Service.created_at,
    }
    column = columns[sort]
    return query.order_by(column.desc().nullslast() if direction == SortDirection.DESC else column.asc().nullslast())


def partner_rows_query() -> Select:
    return (
        select(
            PriceItemVersion.partner_name,
            func.count(distinct(PriceItemVersion.service_id)).label("service_count"),
            func.count(PriceItemVersion.id).label("active_price_count"),
        )
        .where(PriceItemVersion.is_active.is_(True), PriceItemVersion.partner_name.is_not(None))
        .group_by(PriceItemVersion.partner_name)
    )


def count_for(db: Session, query: Select) -> int:
    return int(db.scalar(select(func.count()).select_from(query.order_by(None).subquery())) or 0)


def paginate(query: Select, page: int, page_size: int) -> Select:
    return query.offset((page - 1) * page_size).limit(page_size)


def slice_items(items: list, page: int, page_size: int):
    start = (page - 1) * page_size
    return items[start : start + page_size]


def page_meta(page: int, page_size: int, total: int) -> PageMeta:
    pages = (total + page_size - 1) // page_size if total else 0
    return PageMeta(page=page, page_size=page_size, total=total, pages=pages)


def service_summary(service: Service) -> ServiceSummary:
    return ServiceSummary(
        id=service.id,
        name=service.name_ru,
        normalized_name=service.normalized_name,
        code=service.code,
        tariff_code=service.tariff_code,
        category=service.category,
        specialty=service.specialty,
    )


def partner_summary(name: str | None, service_count: int, active_price_count: int) -> PartnerSummary:
    resolved = name or "Unknown"
    return PartnerSummary(
        id=partner_id_for_name(resolved),
        name=resolved,
        service_count=service_count,
        active_price_count=active_price_count,
    )


def partner_service_summary(
    version: PriceItemVersion,
    service: Service | None,
    partner_name: str,
) -> PartnerServiceSummary:
    fallback_service = ServiceSummary(
        id=version.service_id or UUID("00000000-0000-0000-0000-000000000000"),
        name=version.service_name,
        normalized_name=version.normalized_service_name,
        code=version.source_code,
    )
    return PartnerServiceSummary(
        service=service_summary(service) if service else fallback_service,
        partner=partner_summary(partner_name, 1, 1),
        latest_amount=version.amount,
        currency=version.currency,
        effective_date=version.effective_date,
    )


def service_price_payload(db: Session, service_id: UUID) -> dict:
    versions = db.scalars(
        select(PriceItemVersion)
        .where(
            PriceItemVersion.service_id == service_id,
            PriceItemVersion.is_active.is_(True),
        )
        .order_by(PriceItemVersion.effective_date.desc().nullslast(), PriceItemVersion.created_at.desc())
    ).all()
    if not versions:
        return {"partner_count": 0, "active_price_count": 0}
    partner_names = {version.partner_name for version in versions if version.partner_name}
    latest = versions[0]
    return {
        "partner_count": len(partner_names),
        "active_price_count": len(versions),
        "latest_amount": str(latest.amount),
        "latest_currency": latest.currency,
        "latest_effective_date": latest.effective_date.isoformat() if latest.effective_date else None,
    }


def partner_id_for_name(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.casefold()).strip("-")
    if slug:
        return slug
    digest = hashlib.sha256(name.encode("utf-8")).hexdigest()[:12]
    return f"partner-{digest}"


def resolve_partner_name(db: Session, partner_id: str) -> str | None:
    names = db.scalars(
        select(PriceItemVersion.partner_name)
        .where(PriceItemVersion.is_active.is_(True), PriceItemVersion.partner_name.is_not(None))
        .distinct()
    ).all()
    for name in names:
        if partner_id_for_name(name) == partner_id:
            return name
    return None


def partner_sort_key(sort: PartnerSort):
    if sort == PartnerSort.SERVICES:
        return lambda partner: (partner.service_count, partner.name.casefold())
    return lambda partner: partner.name.casefold()


def partner_service_sort_key(sort: ServiceSort):
    if sort == ServiceSort.CODE:
        return lambda item: (item.service.code or "", item.service.name.casefold())
    if sort == ServiceSort.CATEGORY:
        return lambda item: (item.service.category or "", item.service.name.casefold())
    if sort == ServiceSort.CREATED_AT:
        return lambda item: item.effective_date or date.min
    return lambda item: item.service.name.casefold()


def score_text(query: str, *values: str | None) -> float:
    normalized_query = query.casefold().strip()
    joined = " ".join(value or "" for value in values).casefold()
    if not normalized_query:
        return 0.0
    if normalized_query in joined:
        return 1.0
    query_tokens = set(normalized_query.split())
    value_tokens = set(joined.split())
    if not query_tokens or not value_tokens:
        return 0.0
    return round(len(query_tokens & value_tokens) / len(query_tokens | value_tokens), 4)
