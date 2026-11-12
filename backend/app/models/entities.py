from datetime import datetime, date, timezone
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    experience_level: Mapped[str] = mapped_column(String(50), default="Yeni Mezun")
    target_role: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user_skills: Mapped[List["UserSkill"]] = relationship("UserSkill", back_populates="user", cascade="all, delete-orphan")
    cv_analyses: Mapped[List["CVAnalysis"]] = relationship("CVAnalysis", back_populates="user", cascade="all, delete-orphan")
    career_roadmaps: Mapped[List["CareerRoadmap"]] = relationship("CareerRoadmap", back_populates="user", cascade="all, delete-orphan")
    chat_sessions: Mapped[List["ChatSession"]] = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    sector: Mapped[Optional[str]] = mapped_column(String(120), index=True, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    jobs: Mapped[List["Job"]] = relationship("Job", back_populates="company_rel")


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    jobs: Mapped[List["Job"]] = relationship("Job", back_populates="category_rel")


class DataSource(Base):
    __tablename__ = "data_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)  # SYNTHETIC_DEMO | CSV_UPLOAD | OPEN_DATASET
    license_name: Mapped[str] = mapped_column(String(120), default="MIT / Synthetic Demo")
    source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    dataset_imports: Mapped[List["DatasetImport"]] = relationship("DatasetImport", back_populates="data_source", cascade="all, delete-orphan")


class DatasetImport(Base):
    __tablename__ = "dataset_imports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    data_source_id: Mapped[int] = mapped_column(ForeignKey("data_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    total_rows: Mapped[int] = mapped_column(Integer, default=0)
    imported_rows: Mapped[int] = mapped_column(Integer, default=0)
    duplicate_rows: Mapped[int] = mapped_column(Integer, default=0)
    invalid_rows: Mapped[int] = mapped_column(Integer, default=0)
    validation_status: Mapped[str] = mapped_column(String(50), default="VALIDATED")  # VALIDATED | PARTIAL | FAILED
    validation_summary: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    data_source: Mapped["DataSource"] = relationship("DataSource", back_populates="dataset_imports")
    jobs: Mapped[List["Job"]] = relationship("Job", back_populates="dataset_import", cascade="all, delete-orphan")


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        Index("ix_jobs_location_posted_date", "location", "posted_date"),
        Index("ix_jobs_title_sector", "job_title", "sector"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_title: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    normalized_role: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    company_id: Mapped[Optional[int]] = mapped_column(ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True)
    company_name: Mapped[str] = mapped_column(String(255), default="Belirtilmemiş")
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    dataset_import_id: Mapped[Optional[int]] = mapped_column(ForeignKey("dataset_imports.id", ondelete="CASCADE"), nullable=True, index=True)
    location: Mapped[str] = mapped_column(String(120), index=True, default="Belirtilmemiş")
    sector: Mapped[str] = mapped_column(String(120), index=True, default="Teknoloji")
    description: Mapped[str] = mapped_column(Text, nullable=False)
    employment_type: Mapped[str] = mapped_column(String(80), default="Tam Zamanlı")
    remote_type: Mapped[str] = mapped_column(String(80), index=True, default="Hibrit")
    salary_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    salary_max: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(15), default="TRY")
    posted_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    source_name: Mapped[str] = mapped_column(String(150), default="CSV İçe Aktarma")
    content_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    predicted_category: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    company_rel: Mapped[Optional["Company"]] = relationship("Company", back_populates="jobs")
    category_rel: Mapped[Optional["Category"]] = relationship("Category", back_populates="jobs")
    dataset_import: Mapped[Optional["DatasetImport"]] = relationship("DatasetImport", back_populates="jobs")
    job_skills: Mapped[List["JobSkill"]] = relationship("JobSkill", back_populates="job", cascade="all, delete-orphan")


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    aliases: Mapped[list] = mapped_column(JSON, default=list)
    prerequisites: Mapped[list] = mapped_column(JSON, default=list)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    learning_resources: Mapped[list] = mapped_column(JSON, default=list)
    estimated_hours: Mapped[int] = mapped_column(Integer, default=24)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    job_skills: Mapped[List["JobSkill"]] = relationship("JobSkill", back_populates="skill", cascade="all, delete-orphan")
    user_skills: Mapped[List["UserSkill"]] = relationship("UserSkill", back_populates="skill", cascade="all, delete-orphan")


class JobSkill(Base):
    __tablename__ = "job_skills"
    __table_args__ = (
        UniqueConstraint("job_id", "skill_id", name="uq_job_skill"),
        Index("ix_job_skills_skill_id_job_id", "skill_id", "job_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)
    matched_term: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    job: Mapped["Job"] = relationship("Job", back_populates="job_skills")
    skill: Mapped["Skill"] = relationship("Skill", back_populates="job_skills")


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    analysis_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    scope_key: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    sample_size: Mapped[int] = mapped_column(Integer, default=0)
    date_from: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    date_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    includes_demo: Mapped[bool] = mapped_column(Boolean, default=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    model_name: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    model_type: Mapped[str] = mapped_column(String(80), index=True, nullable=False)  # JOB_CLASSIFIER | SKILL_FORECASTER
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    algorithm: Mapped[str] = mapped_column(String(120), nullable=False)
    training_samples: Mapped[int] = mapped_column(Integer, default=0)
    test_samples: Mapped[int] = mapped_column(Integer, default=0)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)  # MAE, RMSE, accuracy, precision, recall, f1_score
    comparison_data: Mapped[list] = mapped_column(JSON, default=list)  # Actual vs Predicted records
    artifact_path: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    is_experimental: Mapped[bool] = mapped_column(Boolean, default=False)
    trained_on_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    trained_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class UserSkill(Base):
    __tablename__ = "user_skills"
    __table_args__ = (
        UniqueConstraint("user_id", "skill_id", name="uq_user_skill"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)
    proficiency_level: Mapped[str] = mapped_column(String(50), default="Orta")  # Başlangıç | Orta | İleri
    source: Mapped[str] = mapped_column(String(50), default="MANUAL")  # MANUAL | CV
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped["User"] = relationship("User", back_populates="user_skills")
    skill: Mapped["Skill"] = relationship("Skill", back_populates="user_skills")


class CVAnalysis(Base):
    __tablename__ = "cv_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    target_role: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    extracted_skills: Mapped[list] = mapped_column(JSON, default=list)
    classified_skills: Mapped[dict] = mapped_column(JSON, default=dict)
    education_entries: Mapped[list] = mapped_column(JSON, default=list)
    experience_entries: Mapped[list] = mapped_column(JSON, default=list)
    estimated_years_exp: Mapped[float] = mapped_column(Float, default=0.0)
    match_score: Mapped[float] = mapped_column(Float, default=0.0)
    matched_skills: Mapped[list] = mapped_column(JSON, default=list)
    missing_skills: Mapped[list] = mapped_column(JSON, default=list)
    learning_priorities: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped[Optional["User"]] = relationship("User", back_populates="cv_analyses")


class CareerRoadmap(Base):
    __tablename__ = "career_roadmaps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    target_role: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    current_level: Mapped[str] = mapped_column(String(60), nullable=False)
    weekly_hours: Mapped[int] = mapped_column(Integer, default=10)
    current_skills: Mapped[list] = mapped_column(JSON, default=list)
    missing_skills: Mapped[list] = mapped_column(JSON, default=list)
    total_estimated_weeks: Mapped[int] = mapped_column(Integer, default=1)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped[Optional["User"]] = relationship("User", back_populates="career_roadmaps")
    items: Mapped[List["RoadmapItem"]] = relationship("RoadmapItem", back_populates="roadmap", cascade="all, delete-orphan", order_by="RoadmapItem.step_order")


class RoadmapItem(Base):
    __tablename__ = "roadmap_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    roadmap_id: Mapped[int] = mapped_column(ForeignKey("career_roadmaps.id", ondelete="CASCADE"), nullable=False, index=True)
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    skill_name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    demand_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    estimated_hours: Mapped[int] = mapped_column(Integer, default=20)
    estimated_weeks: Mapped[int] = mapped_column(Integer, default=2)
    prerequisites: Mapped[list] = mapped_column(JSON, default=list)
    free_resources: Mapped[list] = mapped_column(JSON, default=list)
    milestone_project: Mapped[str] = mapped_column(Text, nullable=False)

    roadmap: Mapped["CareerRoadmap"] = relationship("CareerRoadmap", back_populates="items")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), default="Kariyer ve Piyasa Analiz Sohbeti")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped[Optional["User"]] = relationship("User", back_populates="chat_sessions")
    messages: Mapped[List["ChatMessage"]] = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(30), nullable=False)  # user | assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    engine_used: Mapped[str] = mapped_column(String(80), default="RULE_AND_STATISTICAL_ENGINE")
    evidence_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    session: Mapped["ChatSession"] = relationship("ChatSession", back_populates="messages")
