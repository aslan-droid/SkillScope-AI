from datetime import date, datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class JobCreateRequest(BaseModel):
    job_title: str = Field(..., min_length=2, max_length=255)
    company_name: str = Field(default="Belirtilmemiş", max_length=255)
    location: str = Field(default="İstanbul", max_length=120)
    sector: str = Field(default="Teknoloji", max_length=120)
    description: str = Field(..., min_length=10)
    employment_type: str = Field(default="Tam Zamanlı", max_length=80)
    remote_type: str = Field(default="Hibrit", max_length=80)
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    currency: str = Field(default="TRY", max_length=15)
    posted_date: Optional[date] = None
    source_url: Optional[str] = None
    source_name: str = Field(default="Manuel Giriş", max_length=150)


class JobResponse(BaseModel):
    id: int
    job_title: str
    normalized_role: str
    company_name: str
    location: str
    sector: str
    description: str
    employment_type: str
    remote_type: str
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    currency: str
    posted_date: date
    source_name: str
    source_url: Optional[str] = None
    predicted_category: Optional[str] = None
    is_demo: bool
    skills: List[str] = Field(default_factory=list)


class PaginatedJobsResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[JobResponse]


class SkillCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    category: str = Field(..., min_length=2, max_length=100)
    aliases: List[str] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    estimated_hours: int = Field(default=20, ge=2, le=200)
    learning_resources: List[Dict[str, str]] = Field(default_factory=list)


class SkillExtractRequest(BaseModel):
    text: str = Field(..., min_length=5)


class CareerMatchRequest(BaseModel):
    target_role: str = Field(..., min_length=2, max_length=150)
    current_skills: List[str] = Field(default_factory=list)
    current_level: str = Field(default="Yeni Mezun")


class CareerRoadmapRequest(BaseModel):
    target_role: str = Field(..., min_length=2, max_length=150)
    current_level: str = Field(default="Yeni Mezun", max_length=60)
    current_skills: List[str] = Field(default_factory=list)
    weekly_hours: int = Field(default=10, ge=2, le=60)


class AssistantAskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)
    session_id: Optional[int] = None


class ClassifyJobTextRequest(BaseModel):
    job_title: str = Field(..., min_length=2)
    description: str = Field(..., min_length=10)
    sector: str = Field(default="")
