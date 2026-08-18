"""Pydantic request bodies for /v1/search and /v1/listings."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

Mode = Literal["search", "category", "home", "developer", "detail", "datasafety"]


class SearchRequest(BaseModel):
    mode: Mode = "search"
    q: str | None = None
    category: str | None = None
    developerId: str | None = None
    packageIds: list[str] = Field(default_factory=list)
    detailUrls: list[str] = Field(default_factory=list)
    c: str = "apps"
    hl: str | None = None
    gl: str | None = None
    market: str | None = None
    maxResults: int = 10
    enrichDetails: bool = False
    includeDataSafety: bool = False
    includeReviews: bool = False
    age: str | None = None
    fields: list[str] | None = None

    @field_validator("maxResults")
    @classmethod
    def _cap(cls, v: int) -> int:
        n = int(v or 10)
        return max(1, min(n, 1000))

    @field_validator("packageIds", "detailUrls", mode="before")
    @classmethod
    def _listify(cls, v: Any) -> list[str]:
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        return list(v)


class ListingsRequest(BaseModel):
    packageIds: list[str] = Field(default_factory=list)
    detailUrls: list[str] = Field(default_factory=list)
    hl: str | None = None
    gl: str | None = None
    market: str | None = None
    maxResults: int = 10
    includeDataSafety: bool = False
    includeReviews: bool = False
    fields: list[str] | None = None

    @field_validator("maxResults")
    @classmethod
    def _cap(cls, v: int) -> int:
        n = int(v or 10)
        return max(1, min(n, 1000))

    @field_validator("packageIds", "detailUrls", mode="before")
    @classmethod
    def _listify(cls, v: Any) -> list[str]:
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        return list(v)
