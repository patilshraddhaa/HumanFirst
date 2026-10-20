from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.db.models import Comment, Like, Post, User
from app.db.session import get_session
from app.routes.schemas import (
    PostCommentCreateEnvelope,
    PostCommentCreateRequest,
    PostCommentListEnvelope,
    PostCommentResponse,
    PostDetailResponse,
    PostLikeRequest,
    PostLikeResponse,
    PostListResponse,
    PostSectionUpdateRequest,
    PostUpdateRequest,
    PublicPostDetailResponse,
)
from app.usecases.posts import (
    build_comment_tree,
    delete_ai_section,
    get_owned_post,
    get_post_by_slug as get_export_post_by_slug,
    get_post_section,
    get_post_sections,
    refresh_post_provenance,
    render_post_export_html,
    serialize_post_detail,
    serialize_post_summary,
    serialize_public_post_detail,
    update_ai_section,
    update_post_metadata,
)

router = APIRouter(tags=["posts"])


def _http_error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"error": code, "message": message})


def _parse_post_id(post_id: str) -> UUID:
    try:
        return UUID(post_id)
    except ValueError as exc:
        raise _http_error(status.HTTP_404_NOT_FOUND, "post_not_found", "Post not found") from exc


async def _get_published_post_or_404(session: AsyncSession, post_id: str) -> Post:
    parsed_post_id = _parse_post_id(post_id)
    result = await session.execute(select(Post).where(Post.id == parsed_post_id, Post.published_at.is_not(None)))
    post = result.scalar_one_or_none()
    if post is None:
        raise _http_error(status.HTTP_404_NOT_FOUND, "post_not_found", "Post not found")
    return post


def _hash_fingerprint(fingerprint: str) -> str:
    normalized = fingerprint.strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _build_like_insert_statement(post_id: UUID, fingerprint_hash: str, dialect_name: str):
    insert_fn = postgresql_insert if dialect_name == "postgresql" else sqlite_insert
    return (
        insert_fn(Like)
        .values(post_id=post_id, fingerprint_hash=fingerprint_hash)
        .on_conflict_do_nothing(index_elements=[Like.post_id, Like.fingerprint_hash])
    )


async def _validate_comment_parent(
    session: AsyncSession,
    post_id: str,
    parent_id: UUID | None,
) -> Comment | None:
    if parent_id is None:
        return None

    result = await session.execute(select(Comment).where(Comment.id == parent_id))
    parent = result.scalar_one_or_none()
    if parent is None:
        raise _http_error(
            status.HTTP_404_NOT_FOUND,
            "parent_comment_not_found",
            "Parent comment not found",
        )
    if str(parent.post_id) != post_id:
        raise _http_error(
            status.HTTP_409_CONFLICT,
            "cross_post_parent",
            "Parent comment must belong to the same post",
        )
    if parent.parent_id is not None:
        raise _http_error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "reply_depth_exceeded",
            "Replies may only target top-level comments",
        )
    return parent


async def _refresh_post_engagement_counts(session: AsyncSession, post_id: str) -> tuple[int, int]:
    parsed_post_id = _parse_post_id(post_id)
    like_count_subquery = select(func.count(Like.id)).where(Like.post_id == parsed_post_id).scalar_subquery()
    comment_count_subquery = select(func.count(Comment.id)).where(Comment.post_id == parsed_post_id).scalar_subquery()
    result = await session.execute(
        update(Post)
        .where(Post.id == parsed_post_id)
        .values(
            like_count=like_count_subquery,
            comment_count=comment_count_subquery,
            updated_at=datetime.now(timezone.utc),
        )
        .returning(Post.like_count, Post.comment_count)
    )
    counts = result.one()
    return counts.like_count, counts.comment_count


@router.get("/posts", response_model=PostListResponse, operation_id="listPosts")
async def list_posts(session: AsyncSession = Depends(get_session)) -> PostListResponse:
    result = await session.execute(
        select(Post).where(Post.published_at.is_not(None)).order_by(Post.published_at.desc(), Post.id.desc())
    )
    posts = [serialize_post_summary(post) for post in result.scalars().all()]
    return PostListResponse(items=posts)


@router.get("/posts/{slug}", response_model=PublicPostDetailResponse, operation_id="getPostBySlug")
async def get_post_by_slug(
    slug: str,
    session: AsyncSession = Depends(get_session),
) -> PublicPostDetailResponse:
    post = await get_export_post_by_slug(session, slug)
    sections = await get_post_sections(session, post.draft_id)
    result = await session.execute(
        select(Comment).where(Comment.post_id == post.id).order_by(Comment.created_at.asc(), Comment.id.asc())
    )
    comments = build_comment_tree(list(result.scalars().all()))
    return serialize_public_post_detail(post, sections, comments)


@router.post(
    "/posts/{post_id}/likes",
    response_model=PostLikeResponse,
    operation_id="likePost",
)
async def like_post(
    post_id: str,
    payload: PostLikeRequest,
    session: AsyncSession = Depends(get_session),
) -> PostLikeResponse:
    await _get_published_post_or_404(session, post_id)
    parsed_post_id = _parse_post_id(post_id)
    fingerprint_hash = _hash_fingerprint(payload.fingerprint)
    dialect_name = session.get_bind().dialect.name
    await session.execute(_build_like_insert_statement(parsed_post_id, fingerprint_hash, dialect_name))
    like_count, _ = await _refresh_post_engagement_counts(session, post_id)
    await session.commit()
    return PostLikeResponse(post_id=parsed_post_id, like_count=like_count, liked=True)


@router.delete(
    "/posts/{post_id}/likes",
    response_model=PostLikeResponse,
    operation_id="unlikePost",
)
async def unlike_post(
    post_id: str,
    payload: PostLikeRequest = Body(...),
    session: AsyncSession = Depends(get_session),
) -> PostLikeResponse:
    await _get_published_post_or_404(session, post_id)
    parsed_post_id = _parse_post_id(post_id)
    fingerprint_hash = _hash_fingerprint(payload.fingerprint)
    await session.execute(delete(Like).where(Like.post_id == parsed_post_id, Like.fingerprint_hash == fingerprint_hash))
    like_count, _ = await _refresh_post_engagement_counts(session, post_id)
    await session.commit()
    return PostLikeResponse(post_id=parsed_post_id, like_count=like_count, liked=False)


@router.post(
    "/posts/{post_id}/comments",
    response_model=PostCommentCreateEnvelope,
    status_code=status.HTTP_201_CREATED,
    operation_id="createPostComment",
)
async def create_post_comment(
    post_id: str,
    payload: PostCommentCreateRequest,
    session: AsyncSession = Depends(get_session),
) -> PostCommentCreateEnvelope:
    await _get_published_post_or_404(session, post_id)
    parsed_post_id = _parse_post_id(post_id)
    parent = await _validate_comment_parent(session, post_id, payload.parent_id)
    comment = Comment(
        post_id=parsed_post_id,
        parent_id=parent.id if parent is not None else None,
        author_name=payload.author_name,
        author_email=payload.author_email,
        body=payload.body,
    )
    session.add(comment)
    await session.flush()
    _, comment_count = await _refresh_post_engagement_counts(session, post_id)
    await session.commit()
    await session.refresh(comment)
    return PostCommentCreateEnvelope(comment=PostCommentResponse.model_validate(comment), comment_count=comment_count)


@router.get(
    "/posts/{post_id}/comments",
    response_model=PostCommentListEnvelope,
    operation_id="listPostComments",
)
async def list_post_comments(
    post_id: str,
    session: AsyncSession = Depends(get_session),
) -> PostCommentListEnvelope:
    post = await _get_published_post_or_404(session, post_id)
    parsed_post_id = _parse_post_id(post_id)
    result = await session.execute(
        select(Comment).where(Comment.post_id == parsed_post_id).order_by(Comment.created_at.asc(), Comment.id.asc())
    )
    comments = result.scalars().all()
    return PostCommentListEnvelope(comments=build_comment_tree(list(comments)), comment_count=post.comment_count)


@router.patch("/posts/{post_id}", response_model=PostDetailResponse, operation_id="updatePost")
async def update_post(
    post_id: str,
    payload: PostUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PostDetailResponse:
    post = await get_owned_post(session, post_id, current_user.id)
    update_post_metadata(post, payload)
    sections = await get_post_sections(session, post.draft_id)
    refresh_post_provenance(post, sections)
    await session.commit()
    await session.refresh(post)
    return serialize_post_detail(post, sections)


@router.patch(
    "/posts/{post_id}/sections/{section_id}",
    response_model=PostDetailResponse,
    operation_id="updatePostSection",
)
async def update_post_section(
    post_id: str,
    section_id: str,
    payload: PostSectionUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PostDetailResponse:
    post = await get_owned_post(session, post_id, current_user.id)
    section = await get_post_section(session, post.draft_id, section_id)
    update_ai_section(section, payload)
    sections = await get_post_sections(session, post.draft_id)
    refresh_post_provenance(post, sections)
    await session.commit()
    await session.refresh(post)
    return serialize_post_detail(post, sections)


@router.delete(
    "/posts/{post_id}/sections/{section_id}",
    response_model=PostDetailResponse,
    operation_id="deletePostSection",
)
async def delete_post_section(
    post_id: str,
    section_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PostDetailResponse:
    post = await get_owned_post(session, post_id, current_user.id)
    section = await get_post_section(session, post.draft_id, section_id)
    await delete_ai_section(session, section)
    await session.flush()
    sections = await get_post_sections(session, post.draft_id)
    refresh_post_provenance(post, sections)
    await session.commit()
    await session.refresh(post)
    return serialize_post_detail(post, sections)


@router.get(
    "/posts/{slug}/export",
    response_class=HTMLResponse,
    operation_id="exportPostHtml",
)
async def export_post_html(
    slug: str,
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    post = await get_export_post_by_slug(session, slug)
    sections = await get_post_sections(session, post.draft_id)
    html = render_post_export_html(post, sections, exported_at=datetime.now(timezone.utc))
    return HTMLResponse(
        content=html,
        headers={"Content-Disposition": f'inline; filename="{post.slug}.html"'},
    )
