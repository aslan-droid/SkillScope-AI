import csv
import io
from pathlib import Path
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.ml.classifier import JobClassifierService, SUPPORTED_CATEGORIES
from app.ml.forecaster import SkillForecasterService
from app.models.entities import Category, DatasetImport, Job, Skill, User
from app.nlp.skill_catalog import DEFAULT_SKILLS_CATALOG
from app.services.csv_importer import import_jobs_from_csv_content


def _generate_synthetic_demo_rows() -> List[Dict[str, Any]]:
    """
    Açıkça sentetik olarak etiketlenen (`SYNTHETIC_DEMO`), 8 aylık zaman serisi,
    Türkiye şehirleri (İstanbul, Ankara, İzmir, Gaziantep, Bursa, Kocaeli, Antalya)
    ve farklı teknoloji alanlarını kapsayan 72 adet örnek iş ilanı üretir.
    """
    role_templates = [
        {
            "job_title": "Veri Analisti",
            "sector": "Finans & Bankacılık",
            "employment_type": "Tam Zamanlı",
            "remote_type": "Hibrit",
            "salary_min": 52000,
            "salary_max": 78000,
            "description": (
                "Finansal raporlama ve müşteri analitiği ekibimiz için SQL, Power BI ve ileri Excel "
                "konularında deneyimli Veri Analisti arıyoruz. Python, Pandas ile veri temizleme, "
                "Statistics ve Data Visualization dashboard tasarımı yapacak, Agile süreçlerde "
                "Communication becerisi yüksek çalışma arkadaşı."
            ),
        },
        {
            "job_title": "İş Zekâsı ve Raporlama Uzmanı (Data Analyst)",
            "sector": "E-Ticaret & Perakende",
            "employment_type": "Tam Zamanlı",
            "remote_type": "Uzaktan",
            "salary_min": 48000,
            "salary_max": 72000,
            "description": (
                "E-ticaret büyüme metriklerini analiz etmek üzere SQL, PostgreSQL, Tableau ve Power BI "
                "kullanan, Excel ve Python (Pandas, NumPy) ile kampanya performans analizleri yürüten, "
                "Data Visualization ve Business Analysis yetkinliğine sahip analist."
            ),
        },
        {
            "job_title": "Kıdemli Backend Geliştirici (Python)",
            "sector": "Yazılım & SaaS",
            "employment_type": "Tam Zamanlı",
            "remote_type": "Uzaktan",
            "salary_min": 75000,
            "salary_max": 115000,
            "description": (
                "Yüksek trafikli SaaS platformumuzda Python, PostgreSQL, Redis ve Docker ile mikroservis "
                "mimarisi geliştirecek; Git, Linux ve AWS ortamlarına hakim, SQL sorgu optimizasyonu "
                "ve Agile / Scrum metodolojilerinde tecrübeli yazılım mühendisi."
            ),
        },
        {
            "job_title": "Full-Stack Yazılım Mühendisi (React & TypeScript)",
            "sector": "Yazılım & SaaS",
            "employment_type": "Tam Zamanlı",
            "remote_type": "Hibrit",
            "salary_min": 68000,
            "salary_max": 98000,
            "description": (
                "Modern web uygulamaları geliştirmek için TypeScript, JavaScript, React ve Python/Node.js "
                "kullanan; PostgreSQL, MongoDB, Docker ve Git araçlarına hakim, Scrum takımlarında "
                "etkili Communication kurabilen Full-Stack geliştirici."
            ),
        },
        {
            "job_title": "Yapay Zekâ ve Makine Öğrenmesi Mühendisi",
            "sector": "Yapay Zekâ & Veri",
            "employment_type": "Tam Zamanlı",
            "remote_type": "Hibrit",
            "salary_min": 82000,
            "salary_max": 125000,
            "description": (
                "Ar-Ge merkezimizde Python, Machine Learning, Deep Learning, Scikit-learn ve PyTorch "
                "ile tahminleme ve NLP modelleri geliştirecek; Generative AI, Pandas, NumPy, SQL ve "
                "Docker kullanarak modelleri üretime alacak mühendis."
            ),
        },
        {
            "job_title": "Veri Bilimci (Data Scientist)",
            "sector": "Telekomünikasyon",
            "employment_type": "Tam Zamanlı",
            "remote_type": "Hibrit",
            "salary_min": 78000,
            "salary_max": 118000,
            "description": (
                "Müşteri kayıp (churn) ve talep tahmin modelleri için Python, Pandas, NumPy, Scikit-learn, "
                "Machine Learning ve Statistics kullanan; SQL ve PostgreSQL üzerinde büyük veri sorgulayan, "
                "TensorFlow ve Data Visualization araçlarıyla bulguları sunabilen Veri Bilimci."
            ),
        },
        {
            "job_title": "DevOps ve Bulut Altyapı Mühendisi",
            "sector": "Bulut & Altyapı",
            "employment_type": "Tam Zamanlı",
            "remote_type": "Uzaktan",
            "salary_min": 80000,
            "salary_max": 120000,
            "description": (
                "CI/CD boru hatları ve konteyner orkestrasyonu için Docker, Kubernetes, Linux, Git, "
                "AWS ve Azure servislerini yöneten; Python/Bash otomasyonu, PostgreSQL ve Redis "
                "yüksek erişilebilirlik kurulumlarında deneyimli sistem mühendisi."
            ),
        },
        {
            "job_title": "Kurumsal Yazılım Geliştirici (Java / C#)",
            "sector": "Üretim & Endüstri 4.0",
            "employment_type": "Tam Zamanlı",
            "remote_type": "Ofisten",
            "salary_min": 60000,
            "salary_max": 90000,
            "description": (
                "Endüstriyel otomasyon ve ERP entegrasyon projelerinde Java, C#, SQL, MySQL ve MariaDB "
                "ile kurumsal backend servisleri geliştiren; Git, Docker ve Agile/Scrum süreçlerine "
                "uyumlu yazılım geliştirme uzmanı."
            ),
        },
        {
            "job_title": "Teknik İş Analisti (Business Analyst)",
            "sector": "Finans & Bankacılık",
            "employment_type": "Tam Zamanlı",
            "remote_type": "Hibrit",
            "salary_min": 55000,
            "salary_max": 82000,
            "description": (
                "Dijital bankacılık ürünlerinde Business Analysis, Project Management, Agile ve Scrum "
                "süreçlerini yönetecek; SQL, Excel ve Power BI ile veri doğrulama yapabilen, "
                "güçlü Communication yetkinliğine sahip İş Analisti."
            ),
        },
        {
            "job_title": "Siber Güvenlik ve SOC Analisti",
            "sector": "Siber Güvenlik & Savunma",
            "employment_type": "Tam Zamanlı",
            "remote_type": "Ofisten",
            "salary_min": 65000,
            "salary_max": 96000,
            "description": (
                "Siber güvenlik operasyon merkezinde (SOC) Linux, ağ güvenliği, zafiyet analizi, "
                "SIEM log takibi ve Python otomasyon scriptleri geliştiren; Docker, AWS güvenliği "
                "ve sızma testi süreçlerinde görev alacak Siber Güvenlik Uzmanı."
            ),
        },
    ]

    cities = [
        ("İstanbul", "AnadoluVeri Teknolojileri A.Ş."),
        ("Ankara", "Başkent Savunma ve Bilişim"),
        ("İzmir", "EgeBulut Yazılım"),
        ("Gaziantep", "Güneydoğu Endüstri ve Dijital A.Ş."),
        ("Bursa", "Marmara Otomotiv Teknolojileri"),
        ("Kocaeli", "Teknopark Ar-Ge Sistemleri"),
        ("İstanbul", "Boğaziçi FinTech Çözümleri"),
        ("Gaziantep", "Zeugma Veri ve Analitik Merkezi"),
        ("Ankara", "Merkez Siber Savunma A.Ş."),
    ]

    months = [
        "2026-04-12",
        "2026-05-14",
        "2026-06-15",
        "2026-07-16",
        "2026-08-18",
        "2026-09-19",
        "2026-10-20",
        "2026-11-05",
    ]

    rows: List[Dict[str, Any]] = []
    idx = 0
    for m_idx, posted_date in enumerate(months):
        # Zaman içinde özellikle SQL, Python, Power BI, Docker ve TypeScript talebinde gerçekçi varyasyon oluştur
        count_in_month = 8 + (m_idx % 3)
        for c_idx in range(count_in_month):
            tpl = role_templates[(idx + c_idx) % len(role_templates)]
            city, company = cities[(idx + m_idx) % len(cities)]
            extra_skill_note = ""
            if m_idx >= 3 and c_idx % 2 == 0:
                extra_skill_note = " Ayrıca SQL, Python, Power BI ve Docker entegrasyon süreçlerinde aktif rol alır."
            elif m_idx >= 5 and c_idx % 3 == 0:
                extra_skill_note = " Generative AI, NLP ve TypeScript tabanlı analitik araçlarla çalışır."

            rows.append(
                {
                    "job_title": tpl["job_title"],
                    "company": company,
                    "location": city,
                    "sector": tpl["sector"],
                    "description": f"{tpl['description']}{extra_skill_note} (Referans Dönem: {posted_date[:7]}, Lokasyon: {city}, Şirket: {company} #{idx + 1})",
                    "employment_type": tpl["employment_type"],
                    "salary_min": tpl["salary_min"] + (m_idx * 1000),
                    "salary_max": tpl["salary_max"] + (m_idx * 1500),
                    "currency": "TRY",
                    "remote_type": tpl["remote_type"],
                    "posted_date": posted_date,
                    "source_url": f"https://skillscope.local/demo-jobs/{idx + 1}",
                    "source_name": "SkillScope Sentetik Demo Veri Seti (SYNTHETIC_DEMO)",
                }
            )
            idx += 1

    return rows


def ensure_sample_csv_file() -> Path:
    sample_dir = Path(__file__).resolve().parents[3] / "data" / "sample"
    sample_dir.mkdir(parents=True, exist_ok=True)
    csv_path = sample_dir / "demo_jobs_tr.csv"

    rows = _generate_synthetic_demo_rows()
    fieldnames = [
        "job_title",
        "company",
        "location",
        "sector",
        "description",
        "employment_type",
        "salary_min",
        "salary_max",
        "currency",
        "remote_type",
        "posted_date",
        "source_url",
        "source_name",
    ]
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return csv_path


def seed_skills_and_categories(db: Session) -> int:
    existing_slugs = {s.slug for s in db.query(Skill).all()}
    added = 0
    for item in DEFAULT_SKILLS_CATALOG:
        if item["slug"] not in existing_slugs:
            db.add(
                Skill(
                    name=item["name"],
                    slug=item["slug"],
                    category=item["category"],
                    aliases=item["aliases"],
                    prerequisites=item["prerequisites"],
                    description=item["description"],
                    learning_resources=item["learning_resources"],
                    estimated_hours=item["estimated_hours"],
                    is_active=True,
                )
            )
            added += 1

    existing_cats = {c.name for c in db.query(Category).all()}
    for cat_name in SUPPORTED_CATEGORIES:
        if cat_name not in existing_cats:
            slug = (
                cat_name.lower()
                .replace(" ", "-")
                .replace("ı", "i")
                .replace("ğ", "g")
                .replace("ü", "u")
                .replace("ş", "s")
                .replace("ö", "o")
                .replace("ç", "c")
                .replace("â", "a")
            )
            db.add(Category(name=cat_name, slug=slug, description=f"{cat_name} alanı"))

    # Varsayılan yerel demo kullanıcı
    default_user = db.query(User).filter(User.email == "demo@skillscope.local").first()
    if not default_user:
        db.add(
            User(
                email="demo@skillscope.local",
                full_name="SkillScope Kariyer Kullanıcısı",
                hashed_password=hash_password("SkillScope2026!"),
                experience_level="Yeni Mezun",
                target_role="Veri Analisti",
            )
        )

    db.commit()
    return added


def load_synthetic_demo_dataset(db: Session, force_reload: bool = False) -> Dict[str, Any]:
    """
    Açıkça sentetik olarak etiketlenmiş (`is_demo=True`, `SYNTHETIC_DEMO`)
    başlangıç veri setini yükler ve ML modellerini günceller.
    """
    seed_skills_and_categories(db)
    csv_path = ensure_sample_csv_file()

    if force_reload:
        demo_imports = db.query(DatasetImport).filter(DatasetImport.is_demo.is_(True)).all()
        for imp in demo_imports:
            db.delete(imp)
        db.commit()

    existing_demo = db.query(Job).filter(Job.is_demo.is_(True)).count()
    if existing_demo > 0 and not force_reload:
        return {
            "status": "already_loaded",
            "demo_jobs_count": existing_demo,
            "message": "Sentetik demo veri seti zaten yüklü.",
        }

    csv_text = csv_path.read_text(encoding="utf-8")
    import_result = import_jobs_from_csv_content(
        db=db,
        csv_text=csv_text,
        filename="demo_jobs_tr.csv",
        source_name="SkillScope Sentetik Demo Veri Seti (SYNTHETIC_DEMO)",
        source_type="SYNTHETIC_DEMO",
        license_name="MIT (Açık Etiketli Sentetik Eğitim & Demo Verisi)",
        is_demo=True,
    )

    # Başlangıç sınıflandırma ve tahmin modellerini eğit
    clf_service = JobClassifierService()
    clf_service.train_and_evaluate(db)

    forecaster = SkillForecasterService()
    for top_skill in ("sql", "python", "power-bi"):
        forecaster.forecast_skill_demand(db, top_skill, horizon_months=3, include_demo=True, persist_model_record=True)

    return import_result
