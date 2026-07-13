from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from app.domain.enums import ApplicationStatus

NonEmpty = Annotated[str, Field(min_length=1, max_length=500)]


class JobPostingIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    source: NonEmpty
    external_id: NonEmpty
    title: NonEmpty
    company: NonEmpty
    apply_url: HttpUrl
    location: str = Field(default="", max_length=500)
    description: str = Field(default="", max_length=200_000)

    @field_validator("source")
    @classmethod
    def normalize_source(cls, value: str) -> str:
        return value.lower().replace(" ", "_")


class StatusChange(BaseModel):
    status: ApplicationStatus
    notes: str = Field(default="", max_length=10_000)


class DiscoveryScanRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    source: Literal["greenhouse", "lever", "ashby"]
    board: Annotated[str, Field(min_length=1, max_length=200, pattern=r"^[A-Za-z0-9._-]+$")]
    company: str | None = Field(default=None, max_length=500)


class DiscoveryScanResult(BaseModel):
    source: str
    board: str
    fetched: int
    upserted: int


class JobPostingResponse(BaseModel):
    id: int
    source: str
    external_id: str
    title: str
    company: str
    location: str
    apply_url: str
    description: str
    score: int
    status: ApplicationStatus
    notes: str
    created_at: str
    updated_at: str


class ErrorResponse(BaseModel):
    detail: str


JsonObject = dict[str, Any]
