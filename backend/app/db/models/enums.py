from enum import Enum

from sqlalchemy import Enum as SQLAlchemyEnum


class DraftStatus(str, Enum):
    DRAFT = "DRAFT"
    LOCKED = "LOCKED"


class SectionAuthorType(str, Enum):
    HUMAN = "HUMAN"
    AI = "AI"


class SectionContentType(str, Enum):
    BODY_PARAGRAPH = "BODY_PARAGRAPH"
    EXAMPLE = "EXAMPLE"
    REPHRASE = "REPHRASE"
    CASE_STUDY = "CASE_STUDY"
    KEY_TAKEAWAYS = "KEY_TAKEAWAYS"
    VISUALISE = "VISUALISE"


class SectionCreationSource(str, Enum):
    LOCK_MATERIALIZATION = "LOCK_MATERIALIZATION"
    MCP = "MCP"
    AUTHOR_EDIT = "AUTHOR_EDIT"


def build_enum(enum_class: type[Enum], name: str) -> SQLAlchemyEnum:
    return SQLAlchemyEnum(
        enum_class,
        name=name,
        values_callable=lambda values: [value.value for value in values],
        validate_strings=True,
        create_constraint=True,
    )


draft_status_enum = build_enum(DraftStatus, "draft_status")
section_author_type_enum = build_enum(SectionAuthorType, "section_author_type")
section_content_type_enum = build_enum(SectionContentType, "section_content_type")
section_creation_source_enum = build_enum(SectionCreationSource, "section_creation_source")
