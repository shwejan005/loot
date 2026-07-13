from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    username: str
    email: Optional[str] = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: Optional[str] = None
    created_at: datetime


class ProblemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    platform: str
    external_id: str
    title: str
    difficulty: Optional[str] = None
    url: Optional[str] = None


class SubmissionCreate(BaseModel):
    user_id: int
    problem_id: int
    external_submission_id: Optional[str] = None
    language: Optional[str] = None
    source_code: Optional[str] = None
    runtime_ms: Optional[int] = None
    memory_kb: Optional[int] = None
    accepted: bool = False
    submitted_at: Optional[datetime] = None


class SubmissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    problem_id: int
    language: Optional[str] = None
    accepted: bool
    submitted_at: Optional[datetime] = None


class SubmissionAnalysisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    submission_id: int
    approach: Optional[str] = None
    time_complexity: Optional[str] = None
    space_complexity: Optional[str] = None
    key_insight: Optional[str] = None
    mistake_notes: Optional[str] = None
    analyzed_at: datetime


class KnowledgePageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    problem_id: int
    explanation: Optional[str] = None
    revision_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class TopicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class ConnectionCreate(BaseModel):
    user_id: int
    platform: str
    external_username: str


class PlatformConnectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    platform: str
    external_username: str
    last_synced_at: Optional[datetime] = None
    enabled: bool
