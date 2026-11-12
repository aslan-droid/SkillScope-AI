from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.v1.endpoints import analytics, assistant, career, cv, datasets, jobs, models, skills
from app.core.config import settings
from app.database.session import get_db
from app.models.entities import Job, Skill

api_router = APIRouter()


@api_router.get("/health", tags=["Sistem & Sağlık"], summary="Veritabanı ve servis sağlık durumunu kontrol eder")
def health_check(db: Session = Depends(get_db)):
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    return {
        "status": "healthy" if db_ok else "degraded",
        "project": settings.PROJECT_NAME,
        "environment": settings.APP_ENV,
        "database_connected": db_ok,
        "jobs_count": db.query(Job).count() if db_ok else 0,
        "skills_count": db.query(Skill).count() if db_ok else 0,
    }


api_router.include_router(jobs.router, prefix="/jobs", tags=["İş İlanları (/jobs)"])
api_router.include_router(skills.router, prefix="/skills", tags=["Beceri Sözlüğü ve Keşif (/skills)"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["İş Piyasası Analitiği (/analytics)"])
api_router.include_router(career.router, prefix="/career", tags=["Kariyer Eşleştirme ve Yol Haritası (/career)"])
api_router.include_router(cv.router, prefix="/cv", tags=["CV Analiz Modülü (/cv)"])
api_router.include_router(assistant.router, prefix="/assistant", tags=["Katmanlı AI Asistanı (/assistant)"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["Veri Yönetimi ve CSV İçe Aktarma (/datasets)"])
api_router.include_router(models.router, prefix="/models", tags=["Makine Öğrenmesi Modelleri (/models)"])
