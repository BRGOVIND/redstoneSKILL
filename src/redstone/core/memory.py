"""Typed, serializable representation of a memory."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


def utc_now() -> datetime:
    """Return an aware UTC timestamp."""
    return datetime.now(UTC)


class MemoryType(StrEnum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    PROJECT = "project"
    PREFERENCE = "preference"
    GOAL = "goal"
    DECISION = "decision"
    CONSTRAINT = "constraint"
    RELATIONSHIP = "relationship"


class MemoryStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    SUPERSEDED = "superseded"


class Memory(BaseModel):
    """A provenance-aware fact, event, decision, preference, or instruction."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=8, max_length=128)
    version: int = Field(default=1, ge=1)
    type: MemoryType
    content: str = Field(min_length=1, max_length=20_000)
    summary: str = Field(min_length=1, max_length=1_000)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    observed_at: datetime = Field(default_factory=utc_now)
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    status: MemoryStatus = MemoryStatus.ACTIVE
    source: str = Field(min_length=1, max_length=500)
    project: str | None = Field(default=None, max_length=200)
    tags: list[str] = Field(default_factory=list)
    entities: list[str] = Field(default_factory=list)
    related_memories: list[str] = Field(default_factory=list)
    relationships: dict[str, list[str]] = Field(default_factory=dict)
    supersedes: str | None = None
    superseded_by: str | None = None
    expires_at: datetime | None = None
    access_count: int = Field(default=0, ge=0)
    last_accessed_at: datetime | None = None
    derived_from: list[str] = Field(default_factory=list)

    @field_validator("content", "summary", "source")
    @classmethod
    def normalize_required_text(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if not normalized:
            raise ValueError("must not be blank")
        return normalized

    @field_validator("tags", "entities")
    @classmethod
    def normalize_labels(cls, values: list[str]) -> list[str]:
        return sorted({" ".join(value.split()).lower() for value in values if value.strip()})
