from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime, timezone
from html import escape
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Comment, Draft, Post, Section, SectionAuthorType, User
from app.routes.schemas import (
    PostCommentResponse,
    PostCommentThreadResponse,
    PostDetailResponse,
    PostProvenanceBucketResponse,
    PostProvenanceResponse,
    PostSectionResponse,
    PostSectionUpdateRequest,
    PostSummaryResponse,
    PostUpdateRequest,
    PublicPostDetailResponse,
)


def word_count_for(text: str) -> int:
    return len(text.split())


def utc_iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _http_error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"error": code, "message": message})


def _parse_uuid(value: str, *, code: str, message: str) -> UUID:
    try:
        return UUID(value)
    except ValueError as exc:
        raise _http_error(404, code, message) from exc


def ensure_not_empty_patch(data: dict[str, object | None]) -> None:
    if not any(value is not None for value in data.values()):
        raise _http_error(400, "empty_patch", "At least one field must be supplied.")


async def get_owned_post(session: AsyncSession, post_id: str, author_id: str) -> Post:
    parsed_post_id = _parse_uuid(post_id, code="post_not_found", message="Post was not found.")
    parsed_author_id = UUID(str(author_id))
    result = await session.execute(
        select(Post).where(
            Post.id == parsed_post_id,
            Post.author_id == parsed_author_id,
            Post.published_at.is_not(None),
        )
    )
    post = result.scalar_one_or_none()
    if post is None:
        raise _http_error(404, "post_not_found", "Post was not found.")
    return post


async def get_post_by_slug(session: AsyncSession, slug: str) -> Post:
    result = await session.execute(select(Post).where(Post.slug == slug, Post.published_at.is_not(None)))
    post = result.scalar_one_or_none()
    if post is None:
        raise _http_error(404, "post_not_found", "Post was not found.")
    return post


async def get_owned_draft_for_publish(
    session: AsyncSession,
    draft_id: str,
    author_id: str,
) -> Draft:
    parsed_draft_id = _parse_uuid(draft_id, code="draft_not_found", message="Draft not found")
    parsed_author_id = UUID(str(author_id))
    result = await session.execute(
        select(Draft).where(Draft.id == parsed_draft_id, Draft.author_id == parsed_author_id)
    )
    draft = result.scalar_one_or_none()
    if draft is None:
        raise _http_error(404, "draft_not_found", "Draft not found")
    return draft


async def get_post_sections(session: AsyncSession, draft_id: str | UUID) -> list[Section]:
    parsed_draft_id = UUID(str(draft_id))
    result = await session.execute(
        select(Section)
        .where(Section.draft_id == parsed_draft_id)
        .order_by(Section.ordinal.asc(), Section.created_at.asc(), Section.id.asc())
    )
    return list(result.scalars().all())


async def get_post_section(session: AsyncSession, draft_id: str | UUID, section_id: str) -> Section:
    parsed_draft_id = UUID(str(draft_id))
    parsed_section_id = _parse_uuid(section_id, code="section_not_found", message="Section was not found.")
    result = await session.execute(
        select(Section).where(Section.draft_id == parsed_draft_id, Section.id == parsed_section_id)
    )
    section = result.scalar_one_or_none()
    if section is None:
        raise _http_error(404, "section_not_found", "Section was not found.")
    return section


def update_post_metadata(post: Post, payload: PostUpdateRequest) -> None:
    ensure_not_empty_patch(payload.model_dump())
    if payload.title is not None:
        post.title = payload.title


def _ensure_ai_section(section: Section) -> None:
    if section.author_type == SectionAuthorType.HUMAN:
        raise _http_error(
            409,
            "human_section_immutable",
            "Human sections are locked after draft lock/materialization.",
        )


def update_ai_section(section: Section, payload: PostSectionUpdateRequest) -> None:
    ensure_not_empty_patch(payload.model_dump())
    _ensure_ai_section(section)
    if payload.content is not None:
        section.content = payload.content
        section.word_count = word_count_for(payload.content)
    if payload.content_type is not None:
        section.content_type = payload.content_type


async def delete_ai_section(session: AsyncSession, section: Section) -> None:
    _ensure_ai_section(section)
    await session.execute(delete(Section).where(Section.id == section.id))


def build_comment_tree(rows: list[Comment]) -> list[PostCommentThreadResponse]:
    replies_by_parent: dict[UUID, list[PostCommentResponse]] = defaultdict(list)
    roots: list[Comment] = []

    for row in rows:
        if row.parent_id is None:
            roots.append(row)
            continue
        replies_by_parent[row.parent_id].append(PostCommentResponse.model_validate(row))

    return [
        PostCommentThreadResponse(
            **PostCommentResponse.model_validate(root).model_dump(),
            replies=replies_by_parent.get(root.id, []),
        )
        for root in roots
    ]


def _compute_provenance_summary(sections: list[Section]) -> tuple[int, int, dict[str, object]]:
    by_author_type: dict[str, dict[str, int]] = defaultdict(lambda: {"count": 0, "word_count": 0})
    by_content_type: dict[str, dict[str, int]] = defaultdict(lambda: {"count": 0, "word_count": 0})
    human_word_count = 0
    ai_word_count = 0

    for section in sections:
        author_key = section.author_type.value
        content_key = section.content_type.value
        word_count = section.word_count
        by_author_type[author_key]["count"] += 1
        by_author_type[author_key]["word_count"] += word_count
        by_content_type[content_key]["count"] += 1
        by_content_type[content_key]["word_count"] += word_count

        if section.author_type == SectionAuthorType.HUMAN:
            human_word_count += word_count
        else:
            ai_word_count += word_count

    total_sections = len(sections)
    human_sections = by_author_type.get(SectionAuthorType.HUMAN.value, {}).get("count", 0)
    ai_sections = by_author_type.get(SectionAuthorType.AI.value, {}).get("count", 0)
    summary: dict[str, object] = {
        "total_sections": total_sections,
        "human_sections": human_sections,
        "ai_sections": ai_sections,
        "human_word_count": human_word_count,
        "ai_word_count": ai_word_count,
        "total_word_count": human_word_count + ai_word_count,
        "has_ai_content": ai_sections > 0,
        "by_author_type": [
            {"key": key, "count": values["count"], "word_count": values["word_count"]}
            for key, values in sorted(by_author_type.items())
        ],
        "by_content_type": [
            {"key": key, "count": values["count"], "word_count": values["word_count"]}
            for key, values in sorted(by_content_type.items())
        ],
    }
    return human_word_count, ai_word_count, summary


def refresh_post_provenance(post: Post, sections: list[Section]) -> None:
    human_word_count, ai_word_count, summary = _compute_provenance_summary(sections)
    post.human_word_count = human_word_count
    post.ai_word_count = ai_word_count
    post.provenance_summary = summary


def _serialize_provenance(summary: dict[str, object] | None, post: Post) -> PostProvenanceResponse:
    data = summary or {}
    return PostProvenanceResponse(
        total_sections=int(data.get("total_sections", 0)),
        human_sections=int(data.get("human_sections", 0)),
        ai_sections=int(data.get("ai_sections", 0)),
        human_word_count=int(data.get("human_word_count", post.human_word_count)),
        ai_word_count=int(data.get("ai_word_count", post.ai_word_count)),
        total_word_count=int(data.get("total_word_count", post.human_word_count + post.ai_word_count)),
        has_ai_content=bool(data.get("has_ai_content", post.ai_word_count > 0)),
        by_author_type=[
            PostProvenanceBucketResponse.model_validate(item) for item in data.get("by_author_type", [])
        ],
        by_content_type=[
            PostProvenanceBucketResponse.model_validate(item) for item in data.get("by_content_type", [])
        ],
    )


def serialize_post_summary(post: Post) -> PostSummaryResponse:
    return PostSummaryResponse(
        id=post.id,
        slug=post.slug,
        title=post.title,
        author_display_name=post.author_display_name,
        like_count=post.like_count,
        comment_count=post.comment_count,
        human_word_count=post.human_word_count,
        ai_word_count=post.ai_word_count,
        published_at=post.published_at or post.updated_at,
        provenance=_serialize_provenance(post.provenance_summary, post),
    )


def _serialize_sections(sections: list[Section]) -> list[PostSectionResponse]:
    return [
        PostSectionResponse(
            id=section.id,
            ordinal=section.ordinal,
            author_type=section.author_type,
            content_type=section.content_type,
            content=section.content,
            anchor_human_section_id=section.anchor_human_section_id,
            word_count=section.word_count,
        )
        for section in sections
    ]


def serialize_public_post_detail(
    post: Post,
    sections: list[Section],
    comments: list[PostCommentThreadResponse],
) -> PublicPostDetailResponse:
    return PublicPostDetailResponse(
        id=post.id,
        author_id=post.author_id,
        author_display_name=post.author_display_name,
        slug=post.slug,
        title=post.title,
        like_count=post.like_count,
        comment_count=post.comment_count,
        human_word_count=post.human_word_count,
        ai_word_count=post.ai_word_count,
        provenance=_serialize_provenance(post.provenance_summary, post),
        published_at=post.published_at or post.updated_at,
        updated_at=post.updated_at,
        sections=_serialize_sections(sections),
        comments=comments,
    )


def serialize_post_detail(
    post: Post,
    sections: list[Section],
    comments: list[PostCommentThreadResponse] | None = None,
) -> PostDetailResponse:
    public_detail = serialize_public_post_detail(post, sections, comments or [])
    return PostDetailResponse(**public_detail.model_dump(), draft_id=post.draft_id)


def _slugify_title(title: str | None) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", (title or "").strip().lower()).strip("-")
    return base or "post"


async def generate_unique_post_slug(session: AsyncSession, title: str | None) -> str:
    base_slug = _slugify_title(title)
    slug = base_slug
    suffix = 2

    while True:
        result = await session.execute(select(Post.id).where(Post.slug == slug))
        if result.scalar_one_or_none() is None:
            return slug
        slug = f"{base_slug}-{suffix}"
        suffix += 1


async def create_published_post(
    session: AsyncSession,
    draft: Draft,
    author: User,
    sections: list[Section],
) -> Post:
    if draft.locked_at is None:
        raise _http_error(409, "draft_not_publishable", "Draft is not publishable")
    if not sections:
        raise _http_error(409, "draft_not_publishable", "Draft is not publishable")

    existing = await session.execute(select(Post.id).where(Post.draft_id == draft.id))
    if existing.scalar_one_or_none() is not None:
        raise _http_error(409, "draft_not_publishable", "Draft is not publishable")

    post = Post(
        draft_id=draft.id,
        author_id=author.id,
        author_display_name=author.display_name or author.name,
        slug=await generate_unique_post_slug(session, draft.title),
        title=(draft.title or "").strip() or "Untitled Post",
        like_count=0,
        comment_count=0,
        published_at=datetime.now(timezone.utc),
    )
    refresh_post_provenance(post, sections)
    session.add(post)
    await session.flush()
    return post


def _render_section_content(content: str) -> str:
    return "<br />".join(escape(line) for line in content.splitlines()) or ""


def _author_label(post: Post) -> str:
    return post.author_display_name or str(post.author_id) or "Unknown author"


def render_post_export_html(post: Post, sections: list[Section], *, exported_at: datetime) -> str:
    author_label = escape(_author_label(post))
    published_at = utc_iso(post.published_at or post.updated_at)
    export_time = utc_iso(exported_at)
    body_parts: list[str] = []
    for section in sections:
        rendered_content = _render_section_content(section.content)
        if section.author_type == SectionAuthorType.HUMAN:
            body_parts.append(f'<section class="section section-human"><p>{rendered_content}</p></section>')
            continue
        label = escape(section.content_type.value.replace("_", " ").title())
        body_parts.append(
            '<aside class="section section-ai">'
            f"<header>AI {label}</header>"
            f'<div class="ai-content">{rendered_content}</div>'
            "</aside>"
        )

    provenance = post.provenance_summary or {}
    human_sections = provenance.get("human_sections", provenance.get("human_section_count", 0))
    ai_sections = provenance.get("ai_sections", provenance.get("ai_section_count", 0))
    return f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{escape(post.title)}</title>
    <style>
      :root {{ color-scheme: light; }}
      body {{ font-family: Georgia, "Times New Roman", serif; margin: 0; background: #f4efe6; color: #1f1a17; }}
      main {{ max-width: 860px; margin: 0 auto; padding: 48px 24px 64px; }}
      article {{ background: #fffdf8; border: 1px solid #d7c8b0; padding: 40px; box-shadow: 0 10px 30px rgba(67, 51, 31, 0.08); }}
      h1 {{ font-size: 2.4rem; margin-bottom: 0.5rem; }}
      .meta, footer {{ color: #5f5246; font-size: 0.95rem; }}
      .section-human p {{ font-size: 1.1rem; line-height: 1.8; margin: 0 0 1.25rem; }}
      .section-ai {{ margin: 1.5rem 0; padding: 1rem 1.25rem; border-left: 4px solid #7f5539; background: #f8efe4; }}
      .section-ai header {{ font-weight: 700; margin-bottom: 0.5rem; letter-spacing: 0.02em; }}
      footer {{ margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #d7c8b0; }}
      ul {{ padding-left: 1.25rem; }}
    </style>
  </head>
  <body>
    <main>
      <article>
        <header>
          <h1>{escape(post.title)}</h1>
          <p class="meta">By {author_label} · Published {published_at} · Slug {escape(post.slug)}</p>
        </header>
        {''.join(body_parts)}
        <footer>
          <h2>Provenance</h2>
          <p>Human sections were locked at draft lock/materialization. AI sections remain marked in this export.</p>
          <ul>
            <li>Author: {author_label}</li>
            <li>Published at: {published_at}</li>
            <li>Exported at: {export_time}</li>
            <li>Slug: {escape(post.slug)}</li>
            <li>Human sections: {human_sections}</li>
            <li>AI sections: {ai_sections}</li>
            <li>Human word count: {provenance.get('human_word_count', 0)}</li>
            <li>AI word count: {provenance.get('ai_word_count', 0)}</li>
          </ul>
        </footer>
      </article>
    </main>
  </body>
</html>"""
