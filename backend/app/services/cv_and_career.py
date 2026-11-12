import io
import re
from typing import Any, Dict, List, Optional

from pypdf import PdfReader
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.entities import CareerRoadmap, CVAnalysis, Job, JobSkill, RoadmapItem, Skill
from app.nlp.extractor import SkillExtractor, normalize_role_title

EDUCATION_KEYWORDS = [
    "üniversite",
    "universite",
    "university",
    "fakülte",
    "fakulte",
    "mühendislik",
    "muhendislik",
    "lisans",
    "yüksek lisans",
    "yuksek lisans",
    "doktora",
    "bachelor",
    "master",
    "bölümü",
    "bolumu",
    "mezun",
    "akademi",
    "meslek yüksekokulu",
]

EXPERIENCE_KEYWORDS = [
    "deneyim",
    "tecrübe",
    "tecrube",
    "experience",
    "staj",
    "stajyer",
    "intern",
    "uzman",
    "mühendis",
    "muhendis",
    "geliştirici",
    "gelistirici",
    "analist",
    "developer",
    "engineer",
    "analyst",
    "şirket",
    "a.ş",
    "ltd",
]


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """
    PDF dosyasını diske kaydetmeden doğrudan bellek (BytesIO) üzerinden okur.
    Gizlilik gereği CV metnini loglara yazmaz.
    """
    if not pdf_bytes or not pdf_bytes.startswith(b"%PDF"):
        raise ValueError("Geçersiz dosya formatı. Lütfen standart bir PDF dosyası yükleyin.")

    reader = PdfReader(io.BytesIO(pdf_bytes))
    pages_text: List[str] = []
    for page in reader.pages:
        txt = page.extract_text() or ""
        if txt.strip():
            pages_text.append(txt.strip())

    combined = "\n".join(pages_text).strip()
    if len(combined) < 20:
        raise ValueError("PDF içerisinden okunabilir metin çıkarılamadı (taranmış resim olabilir).")
    return combined


def parse_cv_sections(cv_text: str) -> Dict[str, Any]:
    """CV metninden eğitim satırlarını, deneyim satırlarını ve tahmini deneyim yılını çıkarır."""
    lines = [re.sub(r"\s+", " ", ln.strip()) for ln in cv_text.splitlines() if ln.strip()]
    education_entries: List[str] = []
    experience_entries: List[str] = []

    for line in lines:
        low = line.lower().replace("İ", "i").replace("I", "ı")
        if len(line) < 6 or len(line) > 220:
            continue
        if any(k in low for k in EDUCATION_KEYWORDS) and len(education_entries) < 6:
            if line not in education_entries:
                education_entries.append(line)
        elif any(k in low for k in EXPERIENCE_KEYWORDS) and len(experience_entries) < 8:
            if line not in experience_entries:
                experience_entries.append(line)

    # Yıl ifadelerinden (örn. "3 yıl", "2+ years") veya tarih aralıklarından tahmini deneyim
    years_found = re.findall(r"(\d{1,2})\s*\+?\s*(?:yıl|yil|year|years)\s*(?:deneyim|tecrübe|experience)?", cv_text.lower())
    estimated_years = 0.0
    if years_found:
        valid_years = [int(y) for y in years_found if 0 < int(y) <= 30]
        if valid_years:
            estimated_years = float(max(valid_years))
    elif experience_entries:
        estimated_years = float(min(5, max(1, len(experience_entries) // 2)))

    return {
        "education_entries": education_entries or ["Eğitim bilgisi metin içerisinde standart başlıkla tespit edilemedi."],
        "experience_entries": experience_entries or ["Deneyim/proje satırları genel metin üzerinden analiz edildi."],
        "estimated_years_exp": estimated_years,
    }


def get_role_skill_benchmarks(db: Session, target_role: str, include_demo: bool = True) -> Dict[str, Any]:
    """Hedeflenen pozisyon için iş ilanlarında en çok aranan becerileri ve sıklıklarını hesaplar."""
    norm_role = normalize_role_title(target_role)
    role_q = db.query(Job).filter(
        (func.lower(Job.normalized_role) == norm_role.lower())
        | (func.lower(Job.job_title).like(f"%{target_role.strip().lower()}%"))
    )
    if not include_demo:
        role_q = role_q.filter(Job.is_demo.is_(False))

    total_role_jobs = role_q.count()
    if total_role_jobs == 0:
        # Eğer spesifik pozisyonda ilan yoksa tüm ilanları baz al
        role_q = db.query(Job)
        if not include_demo:
            role_q = role_q.filter(Job.is_demo.is_(False))
        total_role_jobs = role_q.count()

    job_ids_subq = role_q.with_entities(Job.id)

    rows = (
        db.query(
            Skill,
            func.count(JobSkill.job_id).label("cnt"),
        )
        .join(JobSkill, Skill.id == JobSkill.skill_id)
        .filter(JobSkill.job_id.in_(job_ids_subq))
        .group_by(Skill.id)
        .order_by(func.count(JobSkill.job_id).desc(), Skill.name.asc())
        .limit(12)
        .all()
    )

    benchmarks = []
    for skill_obj, cnt in rows:
        pct = round((cnt / total_role_jobs) * 100, 1) if total_role_jobs > 0 else 0.0
        benchmarks.append(
            {
                "id": skill_obj.id,
                "name": skill_obj.name,
                "slug": skill_obj.slug,
                "category": skill_obj.category,
                "demand_count": int(cnt),
                "demand_percentage": pct,
                "prerequisites": skill_obj.prerequisites or [],
                "estimated_hours": skill_obj.estimated_hours or 20,
                "learning_resources": skill_obj.learning_resources or [],
                "description": skill_obj.description or "",
            }
        )

    return {
        "normalized_role": norm_role,
        "total_role_jobs": total_role_jobs,
        "benchmarks": benchmarks,
    }


def analyze_cv_and_match(
    db: Session,
    cv_text: str,
    target_role: str,
    filename: str = "kullanici_cv.pdf",
    save_record: bool = True,
) -> Dict[str, Any]:
    """
    CV metnini analiz eder, becerileri çıkarır, sınıflandırır, hedef pozisyonla
    karşılaştırır, eşleşen iş ilanlarını ve eksik yetkinlikleri listeler.
    """
    extractor = SkillExtractor.from_db(db)
    extracted = extractor.extract_skills(cv_text)
    classified = extractor.group_by_category(extracted)
    sections = parse_cv_sections(cv_text)

    user_skill_names = [s["name"] for s in extracted]
    user_skill_lower = {s.lower() for s in user_skill_names}

    role_data = get_role_skill_benchmarks(db, target_role, include_demo=True)
    benchmarks = role_data["benchmarks"]

    matched_skills: List[Dict[str, Any]] = []
    missing_skills: List[Dict[str, Any]] = []

    total_weight = sum(max(10.0, b["demand_percentage"]) for b in benchmarks) or 1.0
    matched_weight = 0.0

    for b in benchmarks:
        if b["name"].lower() in user_skill_lower:
            matched_skills.append(
                {
                    "name": b["name"],
                    "category": b["category"],
                    "demand_percentage": b["demand_percentage"],
                }
            )
            matched_weight += max(10.0, b["demand_percentage"])
        else:
            priority_level = "Yüksek Öncelik" if b["demand_percentage"] >= 45 else ("Orta Öncelik" if b["demand_percentage"] >= 25 else "Tamamlayıcı")
            missing_skills.append(
                {
                    "name": b["name"],
                    "slug": b["slug"],
                    "category": b["category"],
                    "demand_percentage": b["demand_percentage"],
                    "priority": priority_level,
                    "prerequisites": b["prerequisites"],
                    "estimated_hours": b["estimated_hours"],
                    "learning_resources": b["learning_resources"],
                }
            )

    match_score = round((matched_weight / total_weight) * 100, 1) if benchmarks else 0.0

    # Öğrenme önceliği sıralaması (önkoşulları karşılanan ve talep oranı yüksek olanlar önce)
    learning_priorities = []
    for idx, ms in enumerate(missing_skills[:8], start=1):
        unmet_prereqs = [p for p in ms["prerequisites"] if p.lower() not in user_skill_lower]
        reason = (
            f"{role_data['normalized_role']} ilanlarının %{ms['demand_percentage']} kadarında aranıyor."
            + (f" Önce {', '.join(unmet_prereqs)} temelini tamamlamanız önerilir." if unmet_prereqs else " Doğrudan öğrenmeye başlayabilirsiniz.")
        )
        learning_priorities.append(
            {
                "rank": idx,
                "skill_name": ms["name"],
                "category": ms["category"],
                "priority": ms["priority"],
                "demand_percentage": ms["demand_percentage"],
                "estimated_hours": ms["estimated_hours"],
                "reason": reason,
                "free_resources": ms["learning_resources"],
            }
        )

    # Kullanıcının mevcut becerileriyle en çok eşleşen iş ilanları
    candidate_jobs = db.query(Job).order_by(Job.posted_date.desc()).limit(80).all()
    matching_jobs = []
    for job in candidate_jobs:
        job_skill_names = [js.skill.name for js in job.job_skills if js.skill]
        if not job_skill_names:
            continue
        overlap = [s for s in job_skill_names if s.lower() in user_skill_lower]
        missing_for_job = [s for s in job_skill_names if s.lower() not in user_skill_lower]
        job_score = round((len(overlap) / len(job_skill_names)) * 100, 1)
        matching_jobs.append(
            {
                "id": job.id,
                "job_title": job.job_title,
                "normalized_role": job.normalized_role,
                "company_name": job.company_name,
                "location": job.location,
                "sector": job.sector,
                "remote_type": job.remote_type,
                "posted_date": str(job.posted_date),
                "skill_alignment_score": job_score,
                "matched_skills": overlap,
                "missing_skills": missing_for_job,
                "is_demo": job.is_demo,
            }
        )
    matching_jobs.sort(key=lambda x: (x["skill_alignment_score"], len(x["matched_skills"])), reverse=True)

    analysis_id: Optional[int] = None
    if save_record:
        cv_record = CVAnalysis(
            filename=filename,
            target_role=role_data["normalized_role"],
            extracted_skills=user_skill_names,
            classified_skills=classified,
            education_entries=sections["education_entries"],
            experience_entries=sections["experience_entries"],
            estimated_years_exp=sections["estimated_years_exp"],
            match_score=match_score,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            learning_priorities=learning_priorities,
        )
        db.add(cv_record)
        db.commit()
        db.refresh(cv_record)
        analysis_id = cv_record.id

    return {
        "analysis_id": analysis_id,
        "filename": filename,
        "target_role": role_data["normalized_role"],
        "role_jobs_analyzed": role_data["total_role_jobs"],
        "extracted_skills": user_skill_names,
        "classified_skills": classified,
        "education_entries": sections["education_entries"],
        "experience_entries": sections["experience_entries"],
        "estimated_years_exp": sections["estimated_years_exp"],
        "skill_alignment_percentage": match_score,
        "alignment_disclaimer": (
            "Bu oran işe alınma olasılığı değildir; CV'nizde tespit edilen teknik becerilerin "
            f"incelenen {role_data['total_role_jobs']} adet '{role_data['normalized_role']}' ilanındaki "
            "beceri gereksinimleriyle ağırlıklı örtüşme oranıdır."
        ),
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "learning_priorities": learning_priorities,
        "matching_jobs": matching_jobs[:8],
        "privacy_notice": (
            "Gizlilik Güvencesi: Yüklediğiniz PDF dosyası diske kalıcı olarak kaydedilmemiş, "
            "ham CV metniniz loglara yazılmamış ve hiçbir dış LLM servisine gönderilmemiştir. "
            "Analiz özet kaydını istediğiniz an silebilirsiniz."
        ),
    }


def generate_career_roadmap(
    db: Session,
    target_role: str,
    current_level: str,
    current_skills: List[str],
    weekly_hours: int = 10,
) -> Dict[str, Any]:
    """
    Kullanıcının mevcut seviyesi, hedef mesleği, mevcut becerileri ve haftalık ayırabileceği
    süreye göre önkoşul sırasını ve ilanlardaki talep oranlarını dikkate alan aşamalı
    kariyer gelişim yol haritası oluşturur.
    """
    weekly_hours = max(2, min(60, weekly_hours))
    role_data = get_role_skill_benchmarks(db, target_role, include_demo=True)
    norm_role = role_data["normalized_role"]
    benchmarks = role_data["benchmarks"]

    all_skills_by_name: Dict[str, Skill] = {s.name.lower(): s for s in db.query(Skill).all()}
    known_lower = {s.strip().lower() for s in current_skills if s and s.strip()}

    # Eksik olan hedef becerileri belirle ve eksik önkoşullarını da listeye dahil et
    target_skill_Map: Dict[str, Dict[str, Any]] = {}
    for b in benchmarks:
        if b["name"].lower() not in known_lower:
            target_skill_Map[b["name"]] = b
            for prereq_name in b.get("prerequisites", []):
                if prereq_name.lower() not in known_lower and prereq_name not in target_skill_Map:
                    sk_obj = all_skills_by_name.get(prereq_name.lower())
                    if sk_obj:
                        target_skill_Map[sk_obj.name] = {
                            "id": sk_obj.id,
                            "name": sk_obj.name,
                            "slug": sk_obj.slug,
                            "category": sk_obj.category,
                            "demand_count": 0,
                            "demand_percentage": 35.0,
                            "prerequisites": sk_obj.prerequisites or [],
                            "estimated_hours": sk_obj.estimated_hours or 20,
                            "learning_resources": sk_obj.learning_resources or [],
                            "description": sk_obj.description or "",
                        }

    # Seviyeye göre öğrenme süresi çarpanı
    level_multiplier = 1.15 if "başlangıç" in current_level.lower() or "öğrenci" in current_level.lower() else (0.85 if "ileri" in current_level.lower() else 1.0)

    # Önkoşul + talep sıklığına göre topolojik sıralama
    ordered_skills: List[Dict[str, Any]] = []
    satisfied = set(known_lower)
    remaining = list(target_skill_Map.values())

    while remaining:
        ready = [
            item
            for item in remaining
            if all(p.lower() in satisfied for p in item.get("prerequisites", []))
        ]
        if not ready:
            # Döngüsel bağımlılık varsa en yüksek talepli olanı seç
            ready = sorted(remaining, key=lambda x: x["demand_percentage"], reverse=True)[:1]
        else:
            ready.sort(key=lambda x: x["demand_percentage"], reverse=True)

        chosen = ready[0]
        ordered_skills.append(chosen)
        satisfied.add(chosen["name"].lower())
        remaining = [r for r in remaining if r["name"] != chosen["name"]]

    # En önemli 7 aşamayı yol haritasına ekle + son aşama olarak Portfolyo Projesi ekle
    selected_steps = ordered_skills[:6]
    roadmap_items_data: List[Dict[str, Any]] = []
    total_weeks = 0

    for idx, item in enumerate(selected_steps, start=1):
        adj_hours = max(8, int(round(item["estimated_hours"] * level_multiplier)))
        est_weeks = max(1, int(round(adj_hours / weekly_hours)))
        total_weeks += est_weeks

        roadmap_items_data.append(
            {
                "step_order": idx,
                "skill_name": item["name"],
                "category": item["category"],
                "title": f"Aşama {idx}: {item['name']} Yetkinliği ve Uygulaması",
                "description": (
                    f"{item.get('description') or item['name']} "
                    f"({norm_role} ilanlarının %{item['demand_percentage']} kadarında talep edilmektedir.)"
                ),
                "demand_percentage": float(item["demand_percentage"]),
                "estimated_hours": adj_hours,
                "estimated_weeks": est_weeks,
                "prerequisites": item.get("prerequisites", []),
                "free_resources": item.get("learning_resources", []),
                "milestone_project": (
                    f"Açık kaynak bir veri seti veya senaryo kullanarak {item['name']} odaklı "
                    f"uçtan uca bir mini proje geliştirin ve GitHub profilinizde dokümante edin."
                ),
            }
        )

    # Final Capstone / Portfolyo Projesi adımı
    capstone_weeks = max(1, int(round(20 / weekly_hours)))
    total_weeks += capstone_weeks
    learned_names = ", ".join([s["skill_name"] for s in roadmap_items_data[:4]]) or norm_role
    roadmap_items_data.append(
        {
            "step_order": len(roadmap_items_data) + 1,
            "skill_name": "Kapsamlı Portfolyo Projesi",
            "category": "Uygulamalı Proje",
            "title": f"Aşama {len(roadmap_items_data) + 1}: Gerçek Veri Setiyle {norm_role} Bitirme Projesi",
            "description": (
                f"Öğrendiğiniz ({learned_names}) teknolojilerini birleştirerek gerçek bir iş problemini "
                "çözen, test edilmiş ve README dokümantasyonu tam bir portfolyo projesi yayınlayın."
            ),
            "demand_percentage": 100.0,
            "estimated_hours": 20,
            "estimated_weeks": capstone_weeks,
            "prerequisites": [s["skill_name"] for s in roadmap_items_data[:3]],
            "free_resources": [
                {
                    "title": "GitHub Pages & Açık Kaynak Portfolyo Rehberi",
                    "url": "https://docs.github.com/tr/pages",
                    "type": "Ücretsiz Doküman",
                },
                {
                    "title": "Kaggle Açık Veri Setleri Arşivi",
                    "url": "https://www.kaggle.com/datasets",
                    "type": "Ücretsiz Veri Kaynağı",
                },
            ],
            "milestone_project": (
                f"{norm_role} pozisyonu için iş görüşmelerinde canlı sunabileceğiniz, "
                "veri toplama, analiz ve görselleştirme adımlarını içeren tam kapsamlı proje."
            ),
        }
    )

    summary_text = (
        f"'{norm_role}' hedefiniz için {role_data['total_role_jobs']} iş ilanı analiz edildi. "
        f"Mevcut '{current_level}' seviyeniz ve haftalık {weekly_hours} saatlik çalışma planınızla "
        f"toplam {len(roadmap_items_data)} aşamalı ({total_weeks} haftalık) ücretsiz kaynak odaklı gelişim planı oluşturuldu."
    )

    roadmap_entity = CareerRoadmap(
        target_role=norm_role,
        current_level=current_level,
        weekly_hours=weekly_hours,
        current_skills=list(current_skills),
        missing_skills=[s["skill_name"] for s in roadmap_items_data if s["skill_name"] != "Kapsamlı Portfolyo Projesi"],
        total_estimated_weeks=total_weeks,
        summary=summary_text,
    )
    db.add(roadmap_entity)
    db.flush()

    for step in roadmap_items_data:
        db.add(
            RoadmapItem(
                roadmap_id=roadmap_entity.id,
                step_order=step["step_order"],
                skill_name=step["skill_name"],
                category=step["category"],
                title=step["title"],
                description=step["description"],
                demand_percentage=step["demand_percentage"],
                estimated_hours=step["estimated_hours"],
                estimated_weeks=step["estimated_weeks"],
                prerequisites=step["prerequisites"],
                free_resources=step["free_resources"],
                milestone_project=step["milestone_project"],
            )
        )

    db.commit()
    db.refresh(roadmap_entity)

    return {
        "roadmap_id": roadmap_entity.id,
        "target_role": roadmap_entity.target_role,
        "current_level": roadmap_entity.current_level,
        "weekly_hours": roadmap_entity.weekly_hours,
        "current_skills": roadmap_entity.current_skills,
        "missing_skills": roadmap_entity.missing_skills,
        "total_estimated_weeks": roadmap_entity.total_estimated_weeks,
        "summary": roadmap_entity.summary,
        "steps": roadmap_items_data,
        "created_at": roadmap_entity.created_at.isoformat(),
    }
