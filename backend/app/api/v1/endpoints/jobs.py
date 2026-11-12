from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import compute_job_fingerprint
from app.database.session import get_db
from app.ml.classifier import infer_reference_category
from app.models.entities import Company, Job, JobSkill, Skill
from app.nlp.extractor import SkillExtractor, normalize_role_title
from app.schemas.api_schemas import JobCreateRequest, JobResponse, PaginatedJobsResponse

router = APIRouter()


def _serialize_job(job: Job) -> JobResponse:
    return JobResponse(
        id=job.id,
        job_title=job.job_title,
        normalized_role=job.normalized_role,
        company_name=job.company_name,
        location=job.location,
        sector=job.sector,
        description=job.description,
        employment_type=job.employment_type,
        remote_type=job.remote_type,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        currency=job.currency,
        posted_date=job.posted_date,
        source_name=job.source_name,
        source_url=job.source_url,
        predicted_category=job.predicted_category,
        is_demo=job.is_demo,
        skills=[js.skill.name for js in job.job_skills if js.skill],
    )


@router.get("", response_model=PaginatedJobsResponse, summary="İş ilanlarını filtreleyerek ve sayfalı olarak listeler")
def list_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    city: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    sector: Optional[str] = Query(None),
    skill: Optional[str] = Query(None),
    remote_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    include_demo: bool = Query(True),
    db: Session = Depends(get_db),
):
    query = db.query(Job)
    if not include_demo:
        query = query.filter(Job.is_demo.is_(False))
    if city and city.lower() != "tümü":
        query = query.filter(func.lower(Job.location) == city.strip().lower())
    if role and role.lower() != "tümü":
        r_like = f"%{role.strip().lower()}%"
        query = query.filter(
            (func.lower(Job.normalized_role).like(r_like)) | (func.lower(Job.job_title).like(r_like))
        )
    if sector and sector.lower() != "tümü":
        query = query.filter(func.lower(Job.sector) == sector.strip().lower())
    if remote_type and remote_type.lower() != "tümü":
        query = query.filter(func.lower(Job.remote_type) == remote_type.strip().lower())
    if search and search.strip():
        s_like = f"%{search.strip().lower()}%"
        query = query.filter(
            (func.lower(Job.job_title).like(s_like))
            | (func.lower(Job.description).like(s_like))
            | (func.lower(Job.company_name).like(s_like))
        )
    if skill and skill.lower() != "tümü":
        sk_clean = skill.strip().lower()
        query = (
            query.join(JobSkill, Job.id == JobSkill.job_id)
            .join(Skill, Skill.id == JobSkill.skill_id)
            .filter((func.lower(Skill.name) == sk_clean) | (func.lower(Skill.slug) == sk_clean))
        )

    total = query.count()
    items = (
        query.order_by(Job.posted_date.desc(), Job.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return PaginatedJobsResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[_serialize_job(j) for j in items],
    )


@router.get("/{job_id}", response_model=JobResponse, summary="Tekil iş ilanı detayını getirir")
def get_job_detail(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="İş ilanı bulunamadı.")
    return _serialize_job(job)


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED, summary="Yeni bir iş ilanı ekler ve becerilerini otomatik çıkarır")
def create_job(payload: JobCreateRequest, db: Session = Depends(get_db)):
    content_hash = compute_job_fingerprint(
        payload.job_title,
        payload.company_name,
        payload.location,
        payload.description,
    )
    existing = db.query(Job).filter(Job.content_hash == content_hash).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bu iş ilanı zaten veritabanında mevcut (Mükerrer kayıt engellendi).",
        )

    company = db.query(Company).filter(func.lower(Company.name) == payload.company_name.strip().lower()).first()
    if not company:
        company = Company(name=payload.company_name.strip(), sector=payload.sector, city=payload.location)
        db.add(company)
        db.flush()

    pred_cat = infer_reference_category(payload.job_title, payload.description, payload.sector)
    job = Job(
        job_title=payload.job_title.strip(),
        normalized_role=normalize_role_title(payload.job_title),
        company_id=company.id,
        company_name=company.name,
        location=payload.location.strip(),
        sector=payload.sector.strip(),
        description=payload.description.strip(),
        employment_type=payload.employment_type,
        remote_type=payload.remote_type,
        salary_min=payload.salary_min,
        salary_max=payload.salary_max,
        currency=payload.currency,
        posted_date=payload.posted_date or date.today(),
        source_url=payload.source_url,
        source_name=payload.source_name,
        content_hash=content_hash,
        is_demo=False,
        predicted_category=pred_cat,
    )
    db.add(job)
    db.flush()

    extractor = SkillExtractor.from_db(db)
    found_skills = extractor.extract_skills(f"{payload.job_title}\n{payload.description}")
    skill_map = {s.slug: s for s in db.query(Skill).all()}
    for sk in found_skills:
        s_entity = skill_map.get(sk["slug"])
        if s_entity:
            db.add(
                JobSkill(
                    job_id=job.id,
                    skill_id=s_entity.id,
                    matched_term=sk.get("matched_term"),
                    confidence=float(sk.get("confidence", 1.0)),
                )
            )

    db.commit()
    db.refresh(job)
    return _serialize_job(job)


@router.delete("/{job_id}", summary="İş ilanını siler")
def delete_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Silinecek ilan bulunamadı.")
    db.delete(job)
    db.commit()
    return {"status": "deleted", "job_id": job_id}
