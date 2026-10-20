from __future__ import annotations

import re
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.db.models import Draft, Section, SectionAuthorType, SectionContentType, SectionCreationSource, User
from app.db.session import get_session
from app.routes.schemas import (
    DraftCreateRequest,
    DraftListResponse,
    DraftResponse,
    DraftUpdateRequest,
    PostDetailResponse,
)
from app.usecases.posts import (
    create_published_post,
    get_owned_draft_for_publish,
    get_post_sections,
    serialize_post_detail,
)

router = APIRouter(tags=["drafts"])


def _draft_not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"error": "draft_not_found", "message": "Draft not found."},
    )


def _draft_locked() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={"error": "draft_locked", "message": "Draft is already locked."},
    )


def _draft_sections_exist() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={"error": "draft_sections_exist", "message": "Draft sections already exist for this draft"},
    )


async def _get_owned_draft(session: AsyncSession, draft_id: str, author_id: str) -> Draft:
    try:
        parsed_draft_id = UUID(draft_id)
    except ValueError:
        raise _draft_not_found()

    result = await session.execute(
        select(Draft).where(Draft.id == parsed_draft_id, Draft.author_id == UUID(str(author_id)))
    )
    draft = result.scalar_one_or_none()
    if draft is None:
        raise _draft_not_found()
    return draft


async def _get_owned_unlocked_draft(session: AsyncSession, draft_id: str, author_id: str) -> Draft:
    draft = await _get_owned_draft(session, draft_id, author_id)
    if draft.locked_at is not None:
        raise _draft_not_found()
    return draft


def _split_body_paragraphs(body: str | None) -> list[str]:
    if body is None:
        return []
    normalized = body.replace("\r\n", "\n").replace("\r", "\n")
    return [paragraph.strip() for paragraph in re.split(r"\n\s*\n+", normalized) if paragraph.strip()]


def _count_words(text: str) -> int:
    return len(text.split())


def _materialize_human_sections(draft: Draft) -> list[Section]:
    return [
        Section(
            draft_id=draft.id,
            ordinal=ordinal,
            author_type=SectionAuthorType.HUMAN,
            content_type=SectionContentType.BODY_PARAGRAPH,
            content=paragraph,
            word_count=_count_words(paragraph),
            created_via=SectionCreationSource.LOCK_MATERIALIZATION,
            position_after_paragraph=ordinal,
        )
        for ordinal, paragraph in enumerate(_split_body_paragraphs(draft.body), start=1)
    ]


@router.post(
    "/drafts",
    response_model=DraftResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="createDraft",
)
async def create_draft(
    payload: DraftCreateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> DraftResponse:
    draft = Draft(
        author_id=current_user.id,
        title=payload.title or "",
        body=payload.body,
        word_count=0,
        keystroke_count=0,
        session_duration_seconds=0,
        pause_events=0,
        paste_attempts=0,
        reading_time_minutes=0,
    )
    session.add(draft)
    await session.commit()
    await session.refresh(draft)
    return DraftResponse.model_validate(draft)


@router.get("/drafts", response_model=DraftListResponse, operation_id="listDrafts")
async def list_drafts(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> DraftListResponse:
    result = await session.execute(
        select(Draft)
        .where(Draft.author_id == current_user.id)
        .order_by(Draft.updated_at.desc(), Draft.id.desc())
    )
    drafts = result.scalars().all()
    return DraftListResponse(items=[DraftResponse.model_validate(draft) for draft in drafts])


@router.get("/drafts/{draft_id}", response_model=DraftResponse, operation_id="getDraft")
async def get_draft(
    draft_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> DraftResponse:
    draft = await _get_owned_draft(session, draft_id, current_user.id)
    return DraftResponse.model_validate(draft)


@router.post("/drafts/{draft_id}/lock", response_model=DraftResponse, operation_id="lockDraft")
async def lock_draft(
    draft_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> DraftResponse:
    draft = await _get_owned_draft(session, draft_id, current_user.id)
    if draft.locked_at is not None:
        raise _draft_locked()

    existing_section = await session.execute(select(Section.id).where(Section.draft_id == draft.id).limit(1))
    if existing_section.scalar_one_or_none() is not None:
        raise _draft_sections_exist()

    session.add_all(_materialize_human_sections(draft))
    draft.locked_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(draft)
    return DraftResponse.model_validate(draft)


@router.patch("/drafts/{draft_id}", response_model=DraftResponse, operation_id="updateDraft")
async def update_draft(
    draft_id: str,
    payload: DraftUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> DraftResponse:
    if not payload.has_updates():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "empty_patch", "message": "Patch payload cannot be empty"},
        )

    draft = await _get_owned_draft(session, draft_id, current_user.id)
    if draft.locked_at is not None:
        raise _draft_locked()
    for field_name in payload.model_fields_set:
        setattr(draft, field_name, getattr(payload, field_name))

    await session.commit()
    await session.refresh(draft)
    return DraftResponse.model_validate(draft)


@router.post(
    "/drafts/{draft_id}/publish",
    response_model=PostDetailResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="publishDraft",
)
async def publish_draft(
    draft_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PostDetailResponse:
    draft = await get_owned_draft_for_publish(session, draft_id, current_user.id)
    sections = await get_post_sections(session, draft.id)
    post = await create_published_post(session, draft, current_user, sections)
    await session.commit()
    await session.refresh(post)
    return serialize_post_detail(post, sections)
