from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.db.models.enums import DraftStatus, SectionAuthorType, SectionContentType


def _normalize_non_empty(value: str, *, field_name: str, max_length: int) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} is required")
    if len(normalized) > max_length:
        raise ValueError(f"{field_name} must be at most {max_length} characters")
    return normalized


def _validate_email(value: str) -> str:
    normalized = _normalize_non_empty(value, field_name="author_email", max_length=320)
    if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
        raise ValueError("author_email must be a valid email address")
    return normalized


class HealthResponse(BaseModel):
    status: str


class DraftCreateRequest(BaseModel):
    title: str | None = None
    body: str = ""


class DraftUpdateRequest(BaseModel):
    title: str | None = None
    body: str | None = None
    word_count: int | None = Field(default=None, ge=0)
    keystroke_count: int | None = Field(default=None, ge=0)
    session_duration_seconds: int | None = Field(default=None, ge=0)
    pause_events: int | None = Field(default=None, ge=0)
    paste_attempts: int | None = Field(default=None, ge=0)
    reading_time_minutes: int | None = Field(default=None, ge=0)

    def has_updates(self) -> bool:
        return bool(self.model_fields_set)


class DraftResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    author_id: UUID
    title: str | None
    body: str
    status: DraftStatus
    word_count: int
    keystroke_count: int
    session_duration_seconds: int
    pause_events: int
    paste_attempts: int
    reading_time_minutes: int
    locked_at: datetime | None
    created_at: datetime
    updated_at: datetime


class DraftListResponse(BaseModel):
    items: list[DraftResponse]


class AuthRegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=1, max_length=1024)


class AuthLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=1024)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str | None = None
    display_name: str | None = None
    email: EmailStr
    mcp_token: str
    created_at: datetime


class AuthSessionResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    user: UserResponse


class AuthMeResponse(BaseModel):
    user: UserResponse


class PostProvenanceBucketResponse(BaseModel):
    key: str
    count: int
    word_count: int


class PostProvenanceResponse(BaseModel):
    total_sections: int
    human_sections: int
    ai_sections: int
    human_word_count: int
    ai_word_count: int
    total_word_count: int
    has_ai_content: bool
    by_author_type: list[PostProvenanceBucketResponse]
    by_content_type: list[PostProvenanceBucketResponse]


class PostSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    title: str
    author_display_name: str | None = None
    like_count: int
    comment_count: int
    human_word_count: int
    ai_word_count: int
    published_at: datetime
    provenance: PostProvenanceResponse


class PostListResponse(BaseModel):
    items: list[PostSummaryResponse]


class PostLikeRequest(BaseModel):
    fingerprint: str

    @field_validator("fingerprint")
    @classmethod
    def validate_fingerprint(cls, value: str) -> str:
        return _normalize_non_empty(value, field_name="fingerprint", max_length=255)


class PostLikeResponse(BaseModel):
    post_id: UUID
    like_count: int
    liked: bool


class PostCommentCreateRequest(BaseModel):
    author_name: str
    author_email: str
    body: str
    parent_id: UUID | None = None

    @field_validator("author_name")
    @classmethod
    def validate_author_name(cls, value: str) -> str:
        return _normalize_non_empty(value, field_name="author_name", max_length=120)

    @field_validator("author_email")
    @classmethod
    def validate_author_email(cls, value: str) -> str:
        return _validate_email(value)

    @field_validator("body")
    @classmethod
    def validate_body(cls, value: str) -> str:
        return _normalize_non_empty(value, field_name="body", max_length=5000)


class PostCommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    post_id: UUID
    parent_id: UUID | None
    author_name: str
    body: str
    created_at: datetime


class PostCommentThreadResponse(PostCommentResponse):
    replies: list[PostCommentResponse]


class PostCommentCreateEnvelope(BaseModel):
    comment: PostCommentResponse
    comment_count: int


class PostCommentListEnvelope(BaseModel):
    comments: list[PostCommentThreadResponse]
    comment_count: int


class PostSectionResponse(BaseModel):
    id: UUID
    ordinal: int
    author_type: SectionAuthorType
    content_type: SectionContentType
    content: str
    anchor_human_section_id: UUID | None = None
    word_count: int


class PublicPostDetailResponse(BaseModel):
    id: UUID
    author_id: UUID
    author_display_name: str | None = None
    slug: str
    title: str
    like_count: int
    comment_count: int
    human_word_count: int
    ai_word_count: int
    provenance: PostProvenanceResponse
    published_at: datetime
    updated_at: datetime
    sections: list[PostSectionResponse]
    comments: list[PostCommentThreadResponse]


class PostDetailResponse(PublicPostDetailResponse):
    draft_id: UUID


class PostUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=255)


class PostSectionUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str | None = Field(default=None, min_length=1)
    content_type: SectionContentType | None = None
