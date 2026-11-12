# SkillScope AI — Veritabanı Başlatma ve Demo Veri Yükleme Scripti
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.database.session import Base, SessionLocal, engine
from app.database.seed import load_synthetic_demo_dataset, seed_skills_and_categories


def main() -> None:
    print("[*] PostgreSQL / SQLAlchemy tabloları doğrulanıyor...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        added_skills = seed_skills_and_categories(db)
        print(f"[+] Beceri sözlüğü hazırlandı ({added_skills} yeni beceri eklendi).")
        res = load_synthetic_demo_dataset(db, force_reload=False)
        print("[+] Sentetik Demo Veri Seti ve ML Modelleri durumu:", res)
    finally:
        db.close()


if __name__ == "__main__":
    main()
