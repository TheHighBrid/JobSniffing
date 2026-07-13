from __future__ import annotations

from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator

from app.domain.enums import ApplicationStatus


class JobPostingIn(BaseModel):
    source: str = Field(min_length=1, max_length=80)
    external_id: str = Field(min_length=1, max_length=300)
    title: str = Field(min_length=1, max_length=300)
    company: str = Field(min_length=1, max_length=200)
    apply_url: str = Field(min_length=8, max_length=3000)
    location: str = Field(default="", max_length=300)
    description: str = Field(default="", max_length=200_000)

    @field_validator("source", "external_id", "title", "company", "location")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("apply_url")
    @classmethod
    def valid_url(cls, value: str) -> str:
        value = value.strip()
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("apply_url must be an absolute http(s) URL")
        return value


class StatusChange(BaseModel):
    status: ApplicationStatus
    notes: str = Field(default="", max_length=5000)


class DiscoveryRequest(BaseModel):
    provider: Literal["greenhouse", "lever", "ashby"]
    identifier: str = Field(min_length=1, max_length=120)
    company: str | None = Field(default=None, max_length=200)
    query: str = Field(default="", max_length=200)
    location: str = Field(default="", max_length=200)
    limit: int = Field(default=100, ge=1, le=500)


class ScoringSettings(BaseModel):
    preferred_terms: dict[str, int]
    excluded_terms: list[str] = Field(default_factory=list)
    blacklisted_companies: list[str] = Field(default_factory=list)
    minimum_score: int = Field(default=0, ge=0, le=100)

    @field_validator("preferred_terms")
    @classmethod
    def normalize_terms(cls, value: dict[str, int]) -> dict[str, int]:
        result: dict[str, int] = {}
        for raw_term, raw_weight in value.items():
            term = raw_term.strip().lower()
            weight = int(raw_weight)
            if not term or not 1 <= weight <= 100:
                raise ValueError("preferred terms require a name and weight from 1 to 100")
            result[term] = weight
        if not result:
            raise ValueError("at least one preferred term is required")
        return result

    @field_validator("excluded_terms", "blacklisted_companies")
    @classmethod
    def normalize_lists(cls, values: list[str]) -> list[str]:
        return list(dict.fromkeys(v.strip().lower() for v in values if v.strip()))


class JobImportRequest(BaseModel):
    jobs: list[JobPostingIn] = Field(min_length=1, max_length=1000)
