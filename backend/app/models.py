from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Boolean, Float, Table
from sqlalchemy.orm import relationship

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# Association table: problems <-> topics (many-to-many)
problem_topics = Table(
    "problem_topics",
    Base.metadata,
    Column("problem_id", Integer, ForeignKey("problems.id"), primary_key=True),
    Column("topic_id", Integer, ForeignKey("topics.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    submissions = relationship("Submission", back_populates="user")
    connections = relationship("PlatformConnection", back_populates="user")


class PlatformConnection(Base):
    __tablename__ = "platform_connections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    platform = Column(String(64), nullable=False)  # leetcode, codeforces, ...
    external_username = Column(String(255), nullable=False)
    last_synced_at = Column(DateTime(timezone=True))
    enabled = Column(Boolean, default=True)

    user = relationship("User", back_populates="connections")


class Problem(Base):
    __tablename__ = "problems"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(64), nullable=False)
    external_id = Column(String(255), nullable=False)
    title = Column(String(512), nullable=False)
    difficulty = Column(String(32))  # easy, medium, hard
    url = Column(String(1024))
    created_at = Column(DateTime(timezone=True), default=utcnow)

    topics = relationship("Topic", secondary=problem_topics, back_populates="problems")
    submissions = relationship("Submission", back_populates="problem")
    knowledge_page = relationship("KnowledgePage", back_populates="problem", uselist=False)


class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), unique=True, nullable=False)

    problems = relationship("Problem", secondary=problem_topics, back_populates="topics")


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    problem_id = Column(Integer, ForeignKey("problems.id"), nullable=False)
    external_submission_id = Column(String(255))
    language = Column(String(64))
    source_code = Column(Text)
    runtime_ms = Column(Integer)
    memory_kb = Column(Integer)
    accepted = Column(Boolean, default=False)
    submitted_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=utcnow)

    user = relationship("User", back_populates="submissions")
    problem = relationship("Problem", back_populates="submissions")
    analysis = relationship("SubmissionAnalysis", back_populates="submission", uselist=False)


class SubmissionAnalysis(Base):
    __tablename__ = "submission_analyses"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"), nullable=False)
    approach = Column(Text)
    time_complexity = Column(String(64))
    space_complexity = Column(String(64))
    key_insight = Column(Text)
    mistake_notes = Column(Text)
    embedding = Column(Text)  # JSON-encoded vector for retrieval
    analyzed_at = Column(DateTime(timezone=True), default=utcnow)

    submission = relationship("Submission", back_populates="analysis")


class KnowledgePage(Base):
    __tablename__ = "knowledge_pages"

    id = Column(Integer, primary_key=True, index=True)
    problem_id = Column(Integer, ForeignKey("problems.id"), nullable=False)
    explanation = Column(Text)
    revision_notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    problem = relationship("Problem", back_populates="knowledge_page")


class LearningEvent(Base):
    __tablename__ = "learning_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_type = Column(String(64), nullable=False)  # solved, revised, mistake
    payload = Column(Text)
    created_at = Column(DateTime(timezone=True), default=utcnow)


class RevisionSchedule(Base):
    __tablename__ = "revision_schedules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    knowledge_page_id = Column(Integer, ForeignKey("knowledge_pages.id"), nullable=False)
    next_review_at = Column(DateTime(timezone=True), nullable=False)
    interval_days = Column(Float, default=1.0)
    ease_factor = Column(Float, default=2.5)
