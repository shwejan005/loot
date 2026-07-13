from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class NormalizedSubmission:
    """Platform-agnostic representation of a single submission.

    Every platform client normalizes its API response into this shape so the
    sync worker can ingest uniformly regardless of the source.
    """

    external_id: str
    external_problem_id: str
    title: str
    accepted: bool
    submitted_at: datetime

    language: Optional[str] = None
    source_code: Optional[str] = None
    difficulty: Optional[str] = None
    runtime_ms: Optional[int] = None
    memory_kb: Optional[int] = None
    topics: list[str] = field(default_factory=list)
    url: Optional[str] = None


class PlatformClient:
    """Base class for platform-specific submission fetchers."""

    name: str = "base"

    def __init__(self, username: str, **kwargs: object) -> None:
        self.username = username

    def fetch_recent(self, count: int = 20) -> list[NormalizedSubmission]:
        raise NotImplementedError
