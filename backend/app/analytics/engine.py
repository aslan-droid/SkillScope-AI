from datetime import date
from typing import Any, Dict, List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.entities import DatasetImport, Job, JobSkill, Skill


def _apply_job_filters(
    query,
    city: Optional[str] = None,
    role: Optional[str] = None,
    sector: Optional[str] = None,
    remote_type: Optional[str] = None,
    skill_name: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    include_demo: bool = True,
):
    if not include_demo:
        query = query.filter(Job.is_demo.is_(False))
    if city and city.strip() and city.lower() != "tümü":
        query = query.filter(func.lower(Job.location) == city.strip().lower())
    if role and role.strip() and role.lower() != "tümü":
        role_q = f"%{role.strip().lower()}%"
        query = query.filter(
            (func.lower(Job.normalized_role).like(role_q)) | (func.lower(Job.job_title).like(role_q))
        )
    if sector and sector.strip() and sector.lower() != "tümü":
        query = query.filter(func.lower(Job.sector) == sector.strip().lower())
    if remote_type and remote_type.strip() and remote_type.lower() != "tümü":
        query = query.filter(func.lower(Job.remote_type) == remote_type.strip().lower())
    if date_from:
        query = query.filter(Job.posted_date >= date_from)
    if date_to:
        query = query.filter(Job.posted_date <= date_to)
    if skill_name and skill_name.strip() and skill_name.lower() != "tümü":
        s_clean = skill_name.strip().lower()
        query = (
            query.join(JobSkill, Job.id == JobSkill.job_id)
            .join(Skill, Skill.id == JobSkill.skill_id)
            .filter((func.lower(Skill.name) == s_clean) | (func.lower(Skill.slug) == s_clean))
        )
    return query


def get_dashboard_summary(db: Session, include_demo: bool = True) -> Dict[str, Any]:
    """Ana sayfa Dashboard için tüm gerçek istatistik ve grafikleri üretir."""
    base_q = _apply_job_filters(db.query(Job), include_demo=include_demo)
    total_jobs = base_q.count()

    if total_jobs == 0:
        return {
            "total_jobs": 0,
            "demo_jobs_count": 0,
            "real_jobs_count": 0,
            "unique_companies": 0,
            "unique_cities": 0,
            "remote_ratio": 0.0,
            "hybrid_ratio": 0.0,
            "onsite_ratio": 0.0,
            "date_range": {"min_date": None, "max_date": None},
            "top_skills": [],
            "top_roles": [],
            "sector_distribution": [],
            "city_distribution": [],
            "remote_distribution": [],
            "recent_jobs": [],
            "skill_trends": [],
        }

    demo_count = base_q.filter(Job.is_demo.is_(True)).count()
    real_count = total_jobs - demo_count

    job_ids_subq = base_q.with_entities(Job.id)

    min_date, max_date = (
        db.query(func.min(Job.posted_date), func.max(Job.posted_date))
        .filter(Job.id.in_(job_ids_subq))
        .first()
    )

    unique_companies = (
        db.query(func.count(func.distinct(Job.company_name)))
        .filter(Job.id.in_(job_ids_subq))
        .scalar()
        or 0
    )
    unique_cities = (
        db.query(func.count(func.distinct(Job.location)))
        .filter(Job.id.in_(job_ids_subq))
        .scalar()
        or 0
    )

    # En çok aranan 10 beceri
    skill_rows = (
        db.query(
            Skill.name,
            Skill.slug,
            Skill.category,
            func.count(JobSkill.job_id).label("cnt"),
        )
        .join(JobSkill, Skill.id == JobSkill.skill_id)
        .filter(JobSkill.job_id.in_(job_ids_subq))
        .group_by(Skill.id, Skill.name, Skill.slug, Skill.category)
        .order_by(func.count(JobSkill.job_id).desc(), Skill.name.asc())
        .limit(10)
        .all()
    )
    top_skills = [
        {
            "name": r.name,
            "slug": r.slug,
            "category": r.category,
            "count": int(r.cnt),
            "percentage": round((r.cnt / total_jobs) * 100, 1),
        }
        for r in skill_rows
    ]

    # En çok ilan bulunan pozisyonlar
    role_rows = (
        db.query(Job.normalized_role, func.count(Job.id).label("cnt"))
        .filter(Job.id.in_(job_ids_subq))
        .group_by(Job.normalized_role)
        .order_by(func.count(Job.id).desc())
        .limit(8)
        .all()
    )
    top_roles = [
        {
            "role": r[0],
            "count": int(r[1]),
            "percentage": round((r[1] / total_jobs) * 100, 1),
        }
        for r in role_rows
    ]

    # Sektör dağılımı
    sector_rows = (
        db.query(Job.sector, func.count(Job.id).label("cnt"))
        .filter(Job.id.in_(job_ids_subq))
        .group_by(Job.sector)
        .order_by(func.count(Job.id).desc())
        .all()
    )
    sector_distribution = [
        {
            "sector": r[0] or "Belirtilmemiş",
            "count": int(r[1]),
            "percentage": round((r[1] / total_jobs) * 100, 1),
        }
        for r in sector_rows
    ]

    # Şehir dağılımı
    city_rows = (
        db.query(Job.location, func.count(Job.id).label("cnt"))
        .filter(Job.id.in_(job_ids_subq))
        .group_by(Job.location)
        .order_by(func.count(Job.id).desc())
        .limit(10)
        .all()
    )
    city_distribution = [
        {
            "city": r[0] or "Belirtilmemiş",
            "count": int(r[1]),
            "percentage": round((r[1] / total_jobs) * 100, 1),
        }
        for r in city_rows
    ]

    # Çalışma modeli (Uzaktan / Hibrit / Ofisten)
    remote_rows = (
        db.query(Job.remote_type, func.count(Job.id).label("cnt"))
        .filter(Job.id.in_(job_ids_subq))
        .group_by(Job.remote_type)
        .all()
    )
    remote_map = {str(r[0]): int(r[1]) for r in remote_rows}
    remote_cnt = remote_map.get("Uzaktan", 0)
    hybrid_cnt = remote_map.get("Hibrit", 0)
    onsite_cnt = remote_map.get("Ofisten", 0)

    remote_distribution = [
        {"type": k, "count": v, "percentage": round((v / total_jobs) * 100, 1)}
        for k, v in sorted(remote_map.items(), key=lambda x: x[1], reverse=True)
    ]

    # Son analiz edilen ilanlar
    recent_objs = (
        db.query(Job)
        .filter(Job.id.in_(job_ids_subq))
        .order_by(Job.posted_date.desc(), Job.id.desc())
        .limit(6)
        .all()
    )
    recent_jobs = [
        {
            "id": j.id,
            "job_title": j.job_title,
            "normalized_role": j.normalized_role,
            "company_name": j.company_name,
            "location": j.location,
            "sector": j.sector,
            "remote_type": j.remote_type,
            "posted_date": str(j.posted_date),
            "predicted_category": j.predicted_category,
            "is_demo": j.is_demo,
            "skills": [js.skill.name for js in j.job_skills if js.skill],
        }
        for j in recent_objs
    ]

    # İlk 4 beceri için aylık talep trendi
    top4_names = [s["name"] for s in top_skills[:4]]
    skill_trends = get_skill_monthly_trends(db, job_ids_subq, top4_names)

    return {
        "total_jobs": total_jobs,
        "demo_jobs_count": demo_count,
        "real_jobs_count": real_count,
        "unique_companies": unique_companies,
        "unique_cities": unique_cities,
        "remote_ratio": round((remote_cnt / total_jobs) * 100, 1),
        "hybrid_ratio": round((hybrid_cnt / total_jobs) * 100, 1),
        "onsite_ratio": round((onsite_cnt / total_jobs) * 100, 1),
        "date_range": {
            "min_date": str(min_date) if min_date else None,
            "max_date": str(max_date) if max_date else None,
        },
        "top_skills": top_skills,
        "top_roles": top_roles,
        "sector_distribution": sector_distribution,
        "city_distribution": city_distribution,
        "remote_distribution": remote_distribution,
        "recent_jobs": recent_jobs,
        "skill_trends": skill_trends,
    }


def get_skill_monthly_trends(db: Session, job_ids_subq, skill_names: List[str]) -> List[Dict[str, Any]]:
    if not skill_names:
        return []
    rows = (
        db.query(Job.posted_date, Skill.name)
        .join(JobSkill, Job.id == JobSkill.job_id)
        .join(Skill, Skill.id == JobSkill.skill_id)
        .filter(Job.id.in_(job_ids_subq))
        .filter(Skill.name.in_(skill_names))
        .all()
    )
    month_bucket: Dict[str, Dict[str, int]] = {}
    for posted_dt, s_name in rows:
        if not posted_dt:
            continue
        period_key = f"{posted_dt.year:04d}-{posted_dt.month:02d}"
        if period_key not in month_bucket:
            month_bucket[period_key] = {name: 0 for name in skill_names}
        month_bucket[period_key][s_name] = month_bucket[period_key].get(s_name, 0) + 1

    sorted_periods = sorted(month_bucket.keys())
    result = []
    for p in sorted_periods:
        entry: Dict[str, Any] = {"period": p}
        entry.update(month_bucket[p])
        result.append(entry)
    return result


def get_market_analytics(
    db: Session,
    city: Optional[str] = None,
    role: Optional[str] = None,
    sector: Optional[str] = None,
    remote_type: Optional[str] = None,
    skill_name: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    include_demo: bool = True,
) -> Dict[str, Any]:
    """İş piyasası analizi sayfasındaki çoklu filtreleme ve maaş/trend grafiklerini üretir."""
    filtered_q = _apply_job_filters(
        db.query(Job),
        city=city,
        role=role,
        sector=sector,
        remote_type=remote_type,
        skill_name=skill_name,
        date_from=date_from,
        date_to=date_to,
        include_demo=include_demo,
    )
    job_ids_subq = filtered_q.with_entities(Job.id).distinct()
    total_jobs = db.query(func.count(Job.id)).filter(Job.id.in_(job_ids_subq)).scalar() or 0

    # Filtre seçeneklerini (dropdowns) doldurmak için mevcut benzersiz değerler
    all_cities = [
        r[0]
        for r in db.query(Job.location).distinct().order_by(Job.location.asc()).all()
        if r[0]
    ]
    all_roles = [
        r[0]
        for r in db.query(Job.normalized_role).distinct().order_by(Job.normalized_role.asc()).all()
        if r[0]
    ]
    all_sectors = [
        r[0]
        for r in db.query(Job.sector).distinct().order_by(Job.sector.asc()).all()
        if r[0]
    ]
    all_skills = [
        r[0]
        for r in db.query(Skill.name).order_by(Skill.name.asc()).all()
        if r[0]
    ]

    if total_jobs == 0:
        return {
            "sample_size": 0,
            "date_range": {"min_date": None, "max_date": None},
            "filters_available": {
                "cities": all_cities,
                "roles": all_roles,
                "sectors": all_sectors,
                "skills": all_skills,
                "remote_types": ["Uzaktan", "Hibrit", "Ofisten"],
            },
            "top_skills": [],
            "role_distribution": [],
            "city_comparison": [],
            "sector_distribution": [],
            "remote_distribution": [],
            "salary_analytics": {
                "sufficient_data": False,
                "reason": "Seçilen filtrelerde maaş verisi içeren yeterli ilan bulunamadı.",
                "by_role": [],
            },
            "skill_trends": [],
        }

    min_date, max_date = (
        db.query(func.min(Job.posted_date), func.max(Job.posted_date))
        .filter(Job.id.in_(job_ids_subq))
        .first()
    )

    skill_rows = (
        db.query(Skill.name, Skill.slug, Skill.category, func.count(JobSkill.job_id).label("cnt"))
        .join(JobSkill, Skill.id == JobSkill.skill_id)
        .filter(JobSkill.job_id.in_(job_ids_subq))
        .group_by(Skill.id, Skill.name, Skill.slug, Skill.category)
        .order_by(func.count(JobSkill.job_id).desc())
        .limit(15)
        .all()
    )
    top_skills = [
        {
            "name": r.name,
            "slug": r.slug,
            "category": r.category,
            "count": int(r.cnt),
            "percentage": round((r.cnt / total_jobs) * 100, 1),
        }
        for r in skill_rows
    ]

    role_rows = (
        db.query(Job.normalized_role, func.count(Job.id).label("cnt"))
        .filter(Job.id.in_(job_ids_subq))
        .group_by(Job.normalized_role)
        .order_by(func.count(Job.id).desc())
        .all()
    )
    role_distribution = [
        {"role": r[0], "count": int(r[1]), "percentage": round((r[1] / total_jobs) * 100, 1)}
        for r in role_rows
    ]

    city_rows = (
        db.query(Job.location, func.count(Job.id).label("cnt"))
        .filter(Job.id.in_(job_ids_subq))
        .group_by(Job.location)
        .order_by(func.count(Job.id).desc())
        .all()
    )
    city_comparison = [
        {"city": r[0], "count": int(r[1]), "percentage": round((r[1] / total_jobs) * 100, 1)}
        for r in city_rows
    ]

    sector_rows = (
        db.query(Job.sector, func.count(Job.id).label("cnt"))
        .filter(Job.id.in_(job_ids_subq))
        .group_by(Job.sector)
        .order_by(func.count(Job.id).desc())
        .all()
    )
    sector_distribution = [
        {"sector": r[0], "count": int(r[1]), "percentage": round((r[1] / total_jobs) * 100, 1)}
        for r in sector_rows
    ]

    remote_rows = (
        db.query(Job.remote_type, func.count(Job.id).label("cnt"))
        .filter(Job.id.in_(job_ids_subq))
        .group_by(Job.remote_type)
        .order_by(func.count(Job.id).desc())
        .all()
    )
    remote_distribution = [
        {"type": r[0], "count": int(r[1]), "percentage": round((r[1] / total_jobs) * 100, 1)}
        for r in remote_rows
    ]

    # Maaş analizi (yalnızca maaş bilgisi bulunan ve en az 3 ilan olan pozisyonlar için)
    salary_rows = (
        db.query(
            Job.normalized_role,
            func.count(Job.id).label("cnt"),
            func.avg(Job.salary_min).label("avg_min"),
            func.avg(Job.salary_max).label("avg_max"),
        )
        .filter(Job.id.in_(job_ids_subq))
        .filter(Job.salary_min.isnot(None), Job.salary_max.isnot(None), Job.currency == "TRY")
        .group_by(Job.normalized_role)
        .having(func.count(Job.id) >= 2)
        .order_by(func.avg(Job.salary_max).desc())
        .all()
    )
    total_salary_samples = sum(int(r.cnt) for r in salary_rows)
    salary_analytics = {
        "sufficient_data": total_salary_samples >= 5,
        "sample_size": total_salary_samples,
        "currency": "TRY",
        "reason": (
            None
            if total_salary_samples >= 5
            else "Güvenilir maaş dağılımı için en az 5 maaş bilgili ilan gereklidir."
        ),
        "by_role": [
            {
                "role": r.normalized_role,
                "count": int(r.cnt),
                "avg_min": round(float(r.avg_min or 0), 0),
                "avg_max": round(float(r.avg_max or 0), 0),
                "avg_midpoint": round((float(r.avg_min or 0) + float(r.avg_max or 0)) / 2, 0),
            }
            for r in salary_rows
        ],
    }

    top5_skill_names = [s["name"] for s in top_skills[:5]]
    skill_trends = get_skill_monthly_trends(db, job_ids_subq, top5_skill_names)

    return {
        "sample_size": total_jobs,
        "date_range": {
            "min_date": str(min_date) if min_date else None,
            "max_date": str(max_date) if max_date else None,
        },
        "filters_available": {
            "cities": all_cities,
            "roles": all_roles,
            "sectors": all_sectors,
            "skills": all_skills,
            "remote_types": ["Uzaktan", "Hibrit", "Ofisten"],
        },
        "top_skills": top_skills,
        "role_distribution": role_distribution,
        "city_comparison": city_comparison,
        "sector_distribution": sector_distribution,
        "remote_distribution": remote_distribution,
        "salary_analytics": salary_analytics,
        "skill_trends": skill_trends,
    }


def get_skill_deep_dive(db: Session, skill_identifier: str, include_demo: bool = True) -> Optional[Dict[str, Any]]:
    """
    Beceri keşfetme sayfası için seçilen becerinin (örn. SQL):
    - İlan sayısı ve toplam içindeki oranı
    - Birlikte en çok arandığı beceriler (co-occurrence)
    - Pozisyonlara göre talebi
    - Sektörlere ve şehirlere göre dağılımı
    - Zaman içindeki değişimi
    bilgilerini hesaplar.
    """
    skill = (
        db.query(Skill)
        .filter(
            (func.lower(Skill.slug) == skill_identifier.strip().lower())
            | (func.lower(Skill.name) == skill_identifier.strip().lower())
        )
        .first()
    )
    if not skill:
        return None

    base_jobs_q = db.query(Job)
    if not include_demo:
        base_jobs_q = base_jobs_q.filter(Job.is_demo.is_(False))
    total_jobs = base_jobs_q.count()

    skill_jobs_q = (
        base_jobs_q.join(JobSkill, Job.id == JobSkill.job_id)
        .filter(JobSkill.skill_id == skill.id)
    )
    skill_job_ids_subq = skill_jobs_q.with_entities(Job.id)
    demand_count = db.query(func.count(Job.id)).filter(Job.id.in_(skill_job_ids_subq)).scalar() or 0

    # Birlikte aranan beceriler (Co-occurrence)
    co_rows = (
        db.query(
            Skill.name,
            Skill.slug,
            Skill.category,
            func.count(JobSkill.job_id).label("cnt"),
        )
        .join(JobSkill, Skill.id == JobSkill.skill_id)
        .filter(JobSkill.job_id.in_(skill_job_ids_subq))
        .filter(Skill.id != skill.id)
        .group_by(Skill.id, Skill.name, Skill.slug, Skill.category)
        .order_by(func.count(JobSkill.job_id).desc())
        .limit(10)
        .all()
    )
    co_occurring_skills = [
        {
            "name": r.name,
            "slug": r.slug,
            "category": r.category,
            "co_count": int(r.cnt),
            "co_percentage": round((r.cnt / demand_count) * 100, 1) if demand_count > 0 else 0.0,
        }
        for r in co_rows
    ]

    # Pozisyonlara göre dağılım
    role_rows = (
        db.query(Job.normalized_role, func.count(Job.id).label("cnt"))
        .filter(Job.id.in_(skill_job_ids_subq))
        .group_by(Job.normalized_role)
        .order_by(func.count(Job.id).desc())
        .limit(8)
        .all()
    )
    by_role = [
        {
            "role": r[0],
            "count": int(r[1]),
            "percentage": round((r[1] / demand_count) * 100, 1) if demand_count > 0 else 0.0,
        }
        for r in role_rows
    ]

    # Sektörlere göre dağılım
    sector_rows = (
        db.query(Job.sector, func.count(Job.id).label("cnt"))
        .filter(Job.id.in_(skill_job_ids_subq))
        .group_by(Job.sector)
        .order_by(func.count(Job.id).desc())
        .limit(8)
        .all()
    )
    by_sector = [
        {
            "sector": r[0],
            "count": int(r[1]),
            "percentage": round((r[1] / demand_count) * 100, 1) if demand_count > 0 else 0.0,
        }
        for r in sector_rows
    ]

    # Şehirlere göre dağılım
    city_rows = (
        db.query(Job.location, func.count(Job.id).label("cnt"))
        .filter(Job.id.in_(skill_job_ids_subq))
        .group_by(Job.location)
        .order_by(func.count(Job.id).desc())
        .limit(8)
        .all()
    )
    by_city = [
        {
            "city": r[0],
            "count": int(r[1]),
            "percentage": round((r[1] / demand_count) * 100, 1) if demand_count > 0 else 0.0,
        }
        for r in city_rows
    ]

    # Zaman içindeki değişim
    monthly_trend = get_skill_monthly_trends(db, skill_job_ids_subq, [skill.name])
    formatted_trend = [
        {"period": item["period"], "count": int(item.get(skill.name, 0))}
        for item in monthly_trend
    ]

    # Örnek ilanlar
    matching_jobs = (
        db.query(Job)
        .filter(Job.id.in_(skill_job_ids_subq))
        .order_by(Job.posted_date.desc())
        .limit(6)
        .all()
    )

    return {
        "skill": {
            "id": skill.id,
            "name": skill.name,
            "slug": skill.slug,
            "category": skill.category,
            "aliases": skill.aliases or [],
            "prerequisites": skill.prerequisites or [],
            "description": skill.description,
            "estimated_hours": skill.estimated_hours,
            "learning_resources": skill.learning_resources or [],
        },
        "total_jobs_analyzed": total_jobs,
        "demand_count": demand_count,
        "demand_percentage": round((demand_count / total_jobs) * 100, 1) if total_jobs > 0 else 0.0,
        "co_occurring_skills": co_occurring_skills,
        "by_role": by_role,
        "by_sector": by_sector,
        "by_city": by_city,
        "monthly_trend": formatted_trend,
        "sample_jobs": [
            {
                "id": j.id,
                "job_title": j.job_title,
                "company_name": j.company_name,
                "location": j.location,
                "sector": j.sector,
                "remote_type": j.remote_type,
                "posted_date": str(j.posted_date),
                "is_demo": j.is_demo,
            }
            for j in matching_jobs
        ],
    }
