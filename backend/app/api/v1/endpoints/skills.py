from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.analytics.engine import get_skill_deep_dive
from app.database.session import get_db
from app.ml.forecaster import SkillForecasterService
from app.models.entities import Job, JobSkill, Skill
from app.nlp.extractor import SkillExtractor
from app.schemas.api_schemas import SkillCreateRequest, SkillExtractRequest

router = APIRouter()


@router.get("", summary="Beceri sözlüğündeki tüm becerileri ve ilanlardaki talep sayılarını listeler")
def list_skills(
    category: Optional[str] = Query(None),
    include_demo: bool = Query(True),
    db: Session = Depends(get_db),
):
    base_jobs_q = db.query(Job)
    if not include_demo:
        base_jobs_q = base_jobs_q.filter(Job.is_demo.is_(False))
    total_jobs = base_jobs_q.count()
    job_ids_subq = base_jobs_q.with_entities(Job.id)

    counts_rows = (
        db.query(JobSkill.skill_id, func.count(JobSkill.job_id))
        .filter(JobSkill.job_id.in_(job_ids_subq))
        .group_by(JobSkill.skill_id)
        .all()
    )
    count_map = {int(r[0]): int(r[1]) for r in counts_rows}

    skills_q = db.query(Skill).filter(Skill.is_active.is_(True))
    if category and category.lower() != "tümü":
        skills_q = skills_q.filter(func.lower(Skill.category) == category.strip().lower())

    skills = skills_q.order_by(Skill.category.asc(), Skill.name.asc()).all()
    items = []
    for s in skills:
        cnt = count_map.get(s.id, 0)
        items.append(
            {
                "id": s.id,
                "name": s.name,
                "slug": s.slug,
                "category": s.category,
                "aliases": s.aliases or [],
                "prerequisites": s.prerequisites or [],
                "description": s.description,
                "estimated_hours": s.estimated_hours,
                "learning_resources": s.learning_resources or [],
                "demand_count": cnt,
                "demand_percentage": round((cnt / total_jobs) * 100, 1) if total_jobs > 0 else 0.0,
            }
        )

    items.sort(key=lambda x: (-x["demand_count"], x["name"]))
    return {"total_skills": len(items), "total_jobs": total_jobs, "items": items}


@router.post("", status_code=status.HTTP_201_CREATED, summary="Beceri sözlüğüne yeni bir beceri ve eş anlamlılarını ekler")
def create_skill(payload: SkillCreateRequest, db: Session = Depends(get_db)):
    slug = (
        payload.name.strip()
        .lower()
        .replace("#", "sharp")
        .replace("+", "p")
        .replace(" ", "-")
        .replace("ı", "i")
        .replace("ğ", "g")
        .replace("ü", "u")
        .replace("ş", "s")
        .replace("ö", "o")
        .replace("ç", "c")
    )
    existing = db.query(Skill).filter((func.lower(Skill.name) == payload.name.strip().lower()) | (Skill.slug == slug)).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Bu beceri zaten sözlükte tanımlı.")

    skill = Skill(
        name=payload.name.strip(),
        slug=slug,
        category=payload.category.strip(),
        aliases=[a.strip() for a in payload.aliases if a.strip()],
        prerequisites=[p.strip() for p in payload.prerequisites if p.strip()],
        description=payload.description,
        estimated_hours=payload.estimated_hours,
        learning_resources=payload.learning_resources,
        is_active=True,
    )
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return {
        "id": skill.id,
        "name": skill.name,
        "slug": skill.slug,
        "category": skill.category,
        "aliases": skill.aliases,
    }


@router.post("/extract", summary="Verilen bir metinden NLP motoruyla becerileri çıkarır ve kategorilere ayırır")
def extract_skills_from_text(payload: SkillExtractRequest, db: Session = Depends(get_db)):
    extractor = SkillExtractor.from_db(db)
    extracted = extractor.extract_skills(payload.text)
    grouped = extractor.group_by_category(extracted)
    return {
        "extracted_count": len(extracted),
        "skills": extracted,
        "grouped_by_category": grouped,
    }


@router.get("/{skill_identifier}", summary="Seçilen beceri için birliktelik, pozisyon, sektör ve trend analizini getirir")
def get_skill_exploration(
    skill_identifier: str,
    include_demo: bool = Query(True),
    db: Session = Depends(get_db),
):
    result = get_skill_deep_dive(db, skill_identifier, include_demo=include_demo)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"'{skill_identifier}' becerisi bulunamadı.")
    forecaster = SkillForecasterService()
    forecast = forecaster.forecast_skill_demand(db, result["skill"]["slug"], horizon_months=3, include_demo=include_demo)
    result["forecast"] = forecast
    return result
