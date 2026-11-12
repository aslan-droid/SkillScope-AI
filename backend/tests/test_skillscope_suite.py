from fastapi.testclient import TestClient

from app.nlp.extractor import SkillExtractor
from tests.conftest import build_minimal_pdf_bytes


def test_health_endpoint(client: TestClient):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["database_connected"] is True
    assert data["jobs_count"] >= 70
    assert data["skills_count"] >= 30


def test_skill_extraction_and_synonyms():
    extractor = SkillExtractor()
    sample_text = (
        "Şirketimizde PowerBI, ms excel, PostgreSQL ve Python3 kullanarak "
        "veri görselleştirme ve makine öğrenmesi modelleri geliştirecek, "
        "C# ve .NET Core bilen, SQL'de ileri seviye uzman arıyoruz."
    )
    extracted = extractor.extract_skills(sample_text)
    names = {item["name"] for item in extracted}

    # PowerBI -> Power BI, ms excel -> Excel, Python3 -> Python, SQL'de -> SQL birleştirilmeli
    assert "Power BI" in names
    assert "Excel" in names
    assert "PostgreSQL" in names
    assert "Python" in names
    assert "Data Visualization" in names
    assert "Machine Learning" in names
    assert "C#" in names
    assert "SQL" in names

    grouped = extractor.group_by_category(extracted)
    assert "Veri Analizi" in grouped
    assert "Programlama" in grouped


def test_csv_upload_validation_and_duplicate_prevention(client: TestClient):
    # Türkçe sütun başlıklarıyla CSV yükleme ve duplicate kontrolü
    csv_content = (
        "ilan_basligi,sirket,sehir,sektor,aciklama,calisma_modeli,yayin_tarihi\n"
        "Veri Analisti Uzmanı,TestCorp A.Ş.,Gaziantep,Teknoloji,\"İleri seviye SQL, Power BI, Python, Pandas ve Excel deneyimi olan analist aranıyor.\",Uzaktan,2026-11-01\n"
        "Veri Analisti Uzmanı,TestCorp A.Ş.,Gaziantep,Teknoloji,\"İleri seviye SQL, Power BI, Python, Pandas ve Excel deneyimi olan analist aranıyor.\",Uzaktan,2026-11-01\n"
        "K,TestCorp,Ankara,Teknoloji,Çok kısa,Ofisten,2026-11-01\n"
    )
    files = {"file": ("test_ilanlar.csv", csv_content.encode("utf-8"), "text/csv")}
    resp = client.post(
        "/api/v1/datasets/upload",
        files=files,
        data={"source_name": "Pytest CSV Testi", "license_name": "MIT"},
    )
    assert resp.status_code == 201
    res = resp.json()
    assert res["total_rows"] == 3
    assert res["imported_rows"] == 1
    assert res["duplicate_rows"] == 1
    assert res["invalid_rows"] == 1
    assert res["extracted_skill_links"] >= 4


def test_csv_missing_required_columns_rejected(client: TestClient):
    bad_csv = "sirket,sehir\nTestFirma,İstanbul\n"
    files = {"file": ("hatali.csv", bad_csv.encode("utf-8"), "text/csv")}
    resp = client.post("/api/v1/datasets/upload", files=files)
    assert resp.status_code == 400
    assert "Zorunlu sütunlar" in resp.json()["detail"]


def test_analytics_dashboard_and_market_filters(client: TestClient):
    dash_resp = client.get("/api/v1/analytics/dashboard")
    assert dash_resp.status_code == 200
    dash = dash_resp.json()
    assert dash["total_jobs"] >= 70
    assert len(dash["top_skills"]) == 10
    assert dash["top_skills"][0]["count"] >= dash["top_skills"][-1]["count"]

    # Şehir ve pozisyon filtresi testi
    market_resp = client.get(
        "/api/v1/analytics/market",
        params={"city": "Gaziantep", "role": "Veri Analisti"},
    )
    assert market_resp.status_code == 200
    market = market_resp.json()
    assert market["sample_size"] >= 1
    assert any(c["city"] == "Gaziantep" for c in market["city_comparison"])


def test_skill_deep_dive_sql(client: TestClient):
    resp = client.get("/api/v1/skills/sql")
    assert resp.status_code == 200
    data = resp.json()
    assert data["skill"]["name"] == "SQL"
    assert data["demand_count"] > 10
    assert len(data["co_occurring_skills"]) > 0
    assert len(data["by_role"]) > 0
    assert "forecast" in data


def test_cv_pdf_extraction_matching_and_deletion(client: TestClient):
    cv_text = (
        "AHMET YILMAZ\n"
        "Gaziantep Universitesi Endustri Muhendisligi Lisans Mezunu\n"
        "Deneyim: 2 yil Veri Analisti Stajyeri - TestTeknoloji A.S.\n"
        "Teknik Beceriler: SQL, PostgreSQL, Python, Excel, Git, Communication\n"
    )
    pdf_bytes = build_minimal_pdf_bytes(cv_text)
    files = {"file": ("ahmet_yilmaz_cv.pdf", pdf_bytes, "application/pdf")}
    resp = client.post(
        "/api/v1/cv/analyze",
        files=files,
        data={"target_role": "Veri Analisti", "save_record": "true"},
    )
    assert resp.status_code == 200
    result = resp.json()
    assert result["target_role"] == "Veri Analisti"
    assert "SQL" in result["extracted_skills"]
    assert "Python" in result["extracted_skills"]
    assert 0 < result["skill_alignment_percentage"] <= 100
    assert "işe alınma olasılığı değildir" in result["alignment_disclaimer"]
    assert len(result["missing_skills"]) > 0

    analysis_id = result["analysis_id"]
    assert analysis_id is not None

    # Kullanıcı CV analizini silebilmeli
    del_resp = client.delete(f"/api/v1/cv/{analysis_id}")
    assert del_resp.status_code == 200


def test_career_roadmap_generation(client: TestClient):
    payload = {
        "target_role": "Veri Analisti",
        "current_level": "Yeni Mezun",
        "current_skills": ["Excel"],
        "weekly_hours": 12,
    }
    resp = client.post("/api/v1/career/roadmap", json=payload)
    assert resp.status_code == 200
    roadmap = resp.json()
    assert roadmap["target_role"] == "Veri Analisti"
    assert len(roadmap["steps"]) >= 3
    step_skills = [s["skill_name"] for s in roadmap["steps"]]
    assert "SQL" in step_skills or "Python" in step_skills


def test_ml_classification_and_forecasting_evaluation(client: TestClient):
    models_resp = client.get("/api/v1/models")
    assert models_resp.status_code == 200
    models_list = models_resp.json()
    assert len(models_list) >= 2

    clf_resp = client.post(
        "/api/v1/models/classify",
        json={
            "job_title": "Kıdemli Veri Analisti",
            "description": "SQL, Power BI, Tableau ve Excel ile finansal dashboard ve istatistiksel raporlama.",
            "sector": "Finans",
        },
    )
    assert clf_resp.status_code == 200
    assert clf_resp.json()["predicted_category"] == "Veri analizi"

    fc_resp = client.get("/api/v1/models/forecast/sql")
    assert fc_resp.status_code == 200
    fc = fc_resp.json()
    assert fc["forecast_available"] is True
    assert "mae" in fc["metrics"]
    assert "rmse" in fc["metrics"]
    assert len(fc["forecast"]) == 3


def test_ai_assistant_evidence_and_fallback_mechanism(client: TestClient):
    ask_resp = client.post(
        "/api/v1/assistant/ask",
        json={"question": "Türkiye'de veri analisti olmak için en çok hangi teknolojiler aranıyor?"},
    )
    assert ask_resp.status_code == 200
    ans = ask_resp.json()
    assert "SQL" in ans["answer"]
    assert ans["evidence"]["sample_size"] > 0
    assert ans["evidence"]["data_period"] != ""
    assert ans["engine_used"] in ("RULE_AND_STATISTICAL_FALLBACK", f"OLLAMA_LOCAL_LLM ({ans['ollama_status']['configured_model']})")
