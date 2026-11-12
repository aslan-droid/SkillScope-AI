from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.api_schemas import CareerMatchRequest, CareerRoadmapRequest
from app.services.cv_and_career import analyze_cv_and_match, generate_career_roadmap, get_role_skill_benchmarks

router = APIRouter()


@router.get("/roles", summary="Hedeflenebilecek ana meslek/pozisyon listesini ve her birinin beceri gereksinimlerini döner")
def list_target_roles(db: Session = Depends(get_db)):
    roles = [
        "Veri Analisti",
        "Veri Bilimci",
        "Yapay Zekâ / ML Mühendisi",
        "Backend Geliştirici",
        "Full-Stack / Yazılım Mühendisi",
        "DevOps & Sistem Mühendisi",
        "Siber Güvenlik Uzmanı",
        "İş Analisti / Ürün Yöneticisi",
    ]
    result = []
    for r in roles:
        bench = get_role_skill_benchmarks(db, r, include_demo=True)
        result.append(
            {
                "role": r,
                "job_count": bench["total_role_jobs"],
                "top_skills": [b["name"] for b in bench["benchmarks"][:6]],
            }
        )
    return {"roles": result}


@router.post("/match", summary="Kullanıcının seçtiği becerileri hedef pozisyonla ve mevcut iş ilanlarıyla eşleştirir")
def match_user_skills_with_role(payload: CareerMatchRequest, db: Session = Depends(get_db)):
    synthetic_text = " ".join(payload.current_skills)
    return analyze_cv_and_match(
        db=db,
        cv_text=synthetic_text,
        target_role=payload.target_role,
        filename="Manuel Beceri Seçimi",
        save_record=False,
    )


@router.post("/roadmap", summary="Kişiselleştirilmiş, önkoşul ve talep odaklı kariyer yol haritası oluşturur")
def create_career_roadmap(payload: CareerRoadmapRequest, db: Session = Depends(get_db)):
    return generate_career_roadmap(
        db=db,
        target_role=payload.target_role,
        current_level=payload.current_level,
        current_skills=payload.current_skills,
        weekly_hours=payload.weekly_hours,
    )
