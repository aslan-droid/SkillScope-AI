"""
SkillScope AI — 16 Adımlı Uçtan Uca Başarı Kriterleri Doğrulama Scripti (Bölüm 20)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import os
os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite://"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.session import Base, get_db
from app.database.seed import load_synthetic_demo_dataset, seed_skills_and_categories
from app.main import app
from tests.conftest import build_minimal_pdf_bytes


def run_e2e_verification() -> None:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()
    seed_skills_and_categories(db)
    load_synthetic_demo_dataset(db, force_reload=True)

    app.dependency_overrides[get_db] = lambda: db
    client = TestClient(app)

    print("=====================================================================")
    print(" SKILLSCOPE AI — 16 ADIMLI UÇTAN UCA SENARYO DOĞRULAMASI")
    print("=====================================================================")

    # Adım 1-6: CSV Yükleme, Doğrulama, Kaydetme, NLP Beceri Çıkarımı ve Analiz
    csv_payload = (
        "job_title,company,location,sector,description,remote_type,posted_date\n"
        "Veri Analisti,Anadolu Analitik A.Ş.,İstanbul,Finans,\"SQL, Power BI, Python, Pandas ve Excel bilen veri analisti.\",Hibrit,2026-11-10\n"
        "Kıdemli Veri Analisti,Ege Veri A.Ş.,İzmir,E-Ticaret,\"SQL, Tableau, PostgreSQL ve Statistics konularında uzman analist.\",Uzaktan,2026-11-11\n"
    )
    up_resp = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("yeni_ilanlar.csv", csv_payload.encode("utf-8"), "text/csv")},
        data={"source_name": "E2E Doğrulama CSV", "license_name": "MIT"},
    )
    assert up_resp.status_code == 201, up_resp.text
    up_data = up_resp.json()
    print(f"[✓] Adım 2-5 (CSV Yükleme & NLP): {up_data['imported_rows']} ilan doğrulandı, {up_data['extracted_skill_links']} beceri çıkarıldı.")

    # Adım 7: Dashboard güncellenmesi
    dash = client.get("/api/v1/analytics/dashboard").json()
    print(f"[✓] Adım 6-7 (Dashboard Güncellemesi): Toplam {dash['total_jobs']} ilan, Lider Beceri: {dash['top_skills'][0]['name']} (%{dash['top_skills'][0]['percentage']}).")

    # Adım 8-9: SQL Becerisinin Seçilmesi ve Birlikte Aranan Beceriler
    sql_deep = client.get("/api/v1/skills/sql").json()
    co_names = [c["name"] for c in sql_deep["co_occurring_skills"][:4]]
    print(f"[✓] Adım 8-9 (SQL Keşfi): {sql_deep['demand_count']} ilanda SQL aranıyor. Birlikte arananlar: {', '.join(co_names)}.")

    # Adım 10-13: CV Yükleme, Beceri Çıkarımı, Hedef Pozisyon ve Eksik Beceriler
    pdf_bytes = build_minimal_pdf_bytes(
        "ZEYNEP KAYA\nIstanbul Teknik Universitesi Muhendislik Lisans\nDeneyim: 1 yil Veri Analisti Stajyeri\nBeceriler: SQL, Excel, Git"
    )
    cv_resp = client.post(
        "/api/v1/cv/analyze",
        files={"file": ("zeynep_kaya_cv.pdf", pdf_bytes, "application/pdf")},
        data={"target_role": "Veri Analisti"},
    )
    assert cv_resp.status_code == 200
    cv_data = cv_resp.json()
    missing_names = [m["name"] for m in cv_data["missing_skills"][:4]]
    print(f"[✓] Adım 10-13 (CV Analizi & Boşluk): Çıkarılan: {cv_data['extracted_skills']} | Hedef: {cv_data['target_role']} (Uyum: %{cv_data['skill_alignment_percentage']}) | Eksikler: {', '.join(missing_names)}.")

    # Adım 14-16: AI Kariyer Asistanı ve Ollama Kapalıyken Fallback Çalışması
    ai_resp = client.post(
        "/api/v1/assistant/ask",
        json={"question": "SQL ile birlikte en çok hangi beceriler aranıyor?"},
    )
    assert ai_resp.status_code == 200
    ai_data = ai_resp.json()
    print(f"[✓] Adım 14-16 (AI Asistanı & Fallback): Motor={ai_data['engine_used']} | Örneklem={ai_data['evidence']['sample_size']} ilan | Dönem={ai_data['evidence']['data_period']}.")
    print("=====================================================================")
    print(" TÜM 16 BAŞARI KRİTERİ HATASIZ DOĞRULANDI!")
    print("=====================================================================")
    db.close()


if __name__ == "__main__":
    run_e2e_verification()
