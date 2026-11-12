from __future__ import annotations

import html
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.ml.classifier import JobClassifierService
from app.models.entities import DataSource, DatasetImport, Job, JobSkill
from app.services.csv_importer import ingest_job_records

REMOTIVE_API_URL = "https://remotive.com/api/remote-jobs"
ARBEITNOW_API_URL = "https://www.arbeitnow.com/api/job-board-api"

SYNC_STATE: Dict[str, Any] = {
    "is_syncing": False,
    "last_sync_at": None,
    "next_sync_at": None,
    "last_sync_status": "idle",
    "last_sync_summary": None,
}


def _strip_html(raw_html: str) -> str:
    """HTML etiketlerini temizleyerek NLP beceri çıkarımına uygun düz metin döndürür."""
    if not raw_html:
        return ""
    unescaped = html.unescape(raw_html)
    cleaned = re.sub(r"<[^>]+>", " ", unescaped)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _parse_salary_text(salary_text: Optional[str]) -> Tuple[Optional[float], Optional[float], str]:
    """Serbest metin maaş bilgisinden (ör. '$70k - $100k') alt/üst sınır ve para birimi çıkarır."""
    if not salary_text:
        return None, None, "USD"

    text = salary_text.strip()
    currency = "USD"
    upper = text.upper()
    if "EUR" in upper or "€" in text:
        currency = "EUR"
    elif "GBP" in upper or "£" in text:
        currency = "GBP"
    elif "TRY" in upper or "TL" in upper or "₺" in text:
        currency = "TRY"

    matches = re.findall(r"(\d+(?:[.,]\d+)?)\s*([kKmM]?)", text)
    values: List[float] = []
    for num_str, suffix in matches:
        try:
            val = float(num_str.replace(",", ""))
        except ValueError:
            continue
        if suffix.lower() == "k":
            val *= 1000
        elif suffix.lower() == "m":
            val *= 1_000_000
        if val >= 1000:
            values.append(val)

    if not values:
        return None, None, currency
    if len(values) == 1:
        return values[0], values[0], currency
    return min(values[0], values[1]), max(values[0], values[1]), currency


def _map_job_type(raw_type: Optional[str]) -> str:
    val = (raw_type or "").lower()
    if "part" in val:
        return "Yarı Zamanlı"
    if "contract" in val or "freelance" in val:
        return "Sözleşmeli"
    if "intern" in val:
        return "Staj"
    return "Tam Zamanlı"


def fetch_remotive_jobs(limit: int = 80, client: Optional[httpx.Client] = None) -> List[Dict[str, Any]]:
    """Remotive açık iş ilanı API'sinden güncel teknoloji ilanlarını çeker."""
    headers = {"User-Agent": "SkillScopeAI/1.0 (+https://github.com/aslan-droid/SkillScope-AI)"}
    own_client = client is None
    http = client or httpx.Client(timeout=20.0, headers=headers)
    try:
        resp = http.get(REMOTIVE_API_URL, params={"limit": limit})
        resp.raise_for_status()
        payload = resp.json()
    finally:
        if own_client:
            http.close()

    records: List[Dict[str, Any]] = []
    for item in payload.get("jobs", [])[:limit]:
        title = (item.get("title") or "").strip()
        tags = item.get("tags") or []
        tag_text = f" Etiketler: {', '.join(tags)}." if isinstance(tags, list) and tags else ""
        desc = _strip_html(item.get("description") or "") + tag_text
        if len(title) < 2 or len(desc) < 10:
            continue

        s_min, s_max, currency = _parse_salary_text(item.get("salary"))
        pub_date = (item.get("publication_date") or "")[:10]
        records.append(
            {
                "job_title": title,
                "description": desc,
                "company": (item.get("company_name") or "Remotive İşvereni").strip(),
                "location": (item.get("candidate_required_location") or "Global / Uzaktan").strip(),
                "sector": (item.get("category") or "Teknoloji").strip(),
                "employment_type": _map_job_type(item.get("job_type")),
                "remote_type": "Uzaktan",
                "salary_min": s_min,
                "salary_max": s_max,
                "currency": currency,
                "posted_date": pub_date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "source_url": item.get("url"),
                "source_name": "Remotive Public API",
            }
        )
    return records


def fetch_arbeitnow_jobs(limit: int = 100, client: Optional[httpx.Client] = None) -> List[Dict[str, Any]]:
    """Arbeitnow açık iş ilanı API'sinden güncel teknoloji ilanlarını çeker."""
    headers = {"User-Agent": "SkillScopeAI/1.0 (+https://github.com/aslan-droid/SkillScope-AI)"}
    own_client = client is None
    http = client or httpx.Client(timeout=20.0, headers=headers)
    try:
        resp = http.get(ARBEITNOW_API_URL)
        resp.raise_for_status()
        payload = resp.json()
    finally:
        if own_client:
            http.close()

    records: List[Dict[str, Any]] = []
    for item in payload.get("data", [])[:limit]:
        title = (item.get("title") or "").strip()
        tags = item.get("tags") or []
        tag_text = f" Etiketler: {', '.join(tags)}." if isinstance(tags, list) and tags else ""
        desc = _strip_html(item.get("description") or "") + tag_text
        if len(title) < 2 or len(desc) < 10:
            continue

        created_val = item.get("created_at")
        posted_dt: Any = None
        if isinstance(created_val, (int, float)):
            posted_dt = datetime.fromtimestamp(created_val, tz=timezone.utc).replace(tzinfo=None)
        elif isinstance(created_val, str) and created_val:
            posted_dt = created_val[:10]

        job_types = item.get("job_types") or []
        emp_raw = job_types[0] if isinstance(job_types, list) and job_types else ""
        is_remote = bool(item.get("remote"))

        records.append(
            {
                "job_title": title,
                "description": desc,
                "company": (item.get("company_name") or "Arbeitnow İşvereni").strip(),
                "location": (item.get("location") or "Avrupa / Uzaktan").strip(),
                "sector": "Teknoloji & Yazılım",
                "employment_type": _map_job_type(emp_raw),
                "remote_type": "Uzaktan" if is_remote else "Ofisten",
                "salary_min": None,
                "salary_max": None,
                "currency": "EUR",
                "posted_date": posted_dt or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "source_url": item.get("url"),
                "source_name": "Arbeitnow Public API",
            }
        )
    return records


def sync_live_sources(
    db: Session,
    sources: Optional[List[str]] = None,
    limit_per_source: int = 80,
    retrain_models: bool = True,
    client: Optional[httpx.Client] = None,
) -> Dict[str, Any]:
    """
    Açık ve yasal iş ilanı API'lerinden (Remotive, Arbeitnow) güncel ilanları çeker,
    mükerrerleri eler, NLP beceri çıkarımı yapar ve gerekirse ML modelini yeniden eğitir.
    """
    if SYNC_STATE["is_syncing"]:
        return {"status": "already_running", "sync_state": SYNC_STATE}

    selected = [s.lower() for s in (sources or ["remotive", "arbeitnow"])]
    SYNC_STATE["is_syncing"] = True
    started_at = datetime.now(timezone.utc)
    source_results: List[Dict[str, Any]] = []
    errors: List[str] = []
    total_imported = 0
    total_duplicates = 0
    total_skill_links = 0

    try:
        fetchers = {
            "remotive": (
                "Remotive Public API",
                "Remotive Public API (Attribution Required)",
                f"remotive_sync_{started_at.strftime('%Y%m%d_%H%M')}.json",
                fetch_remotive_jobs,
            ),
            "arbeitnow": (
                "Arbeitnow Public API",
                "Arbeitnow Public Job Board API",
                f"arbeitnow_sync_{started_at.strftime('%Y%m%d_%H%M')}.json",
                fetch_arbeitnow_jobs,
            ),
        }

        for key in selected:
            if key not in fetchers:
                errors.append(f"Desteklenmeyen kaynak: {key}")
                continue
            source_name, license_name, filename, fetch_fn = fetchers[key]
            try:
                records = fetch_fn(limit=limit_per_source, client=client)
                res = ingest_job_records(
                    db=db,
                    records=records,
                    filename=filename,
                    source_name=source_name,
                    source_type="PUBLIC_API",
                    license_name=license_name,
                    is_demo=False,
                )
                total_imported += res["imported_rows"]
                total_duplicates += res["duplicate_rows"]
                total_skill_links += res["extracted_skill_links"]
                source_results.append(
                    {
                        "source": key,
                        "source_name": source_name,
                        "fetched": len(records),
                        "imported": res["imported_rows"],
                        "duplicates": res["duplicate_rows"],
                        "skill_links": res["extracted_skill_links"],
                        "status": res["validation_status"],
                    }
                )
            except Exception as exc:
                errors.append(f"{source_name}: {str(exc)}")
                source_results.append(
                    {
                        "source": key,
                        "source_name": source_name,
                        "fetched": 0,
                        "imported": 0,
                        "duplicates": 0,
                        "skill_links": 0,
                        "status": "ERROR",
                        "error": str(exc),
                    }
                )

        ml_retrained = False
        ml_metrics: Optional[Dict[str, Any]] = None
        if retrain_models and total_imported > 0:
            try:
                ml_res = JobClassifierService().train_and_evaluate(db)
                ml_retrained = ml_res.get("status") == "trained"
                ml_metrics = ml_res.get("metrics")
            except Exception as exc:
                errors.append(f"Model yeniden eğitimi: {str(exc)}")

        now = datetime.now(timezone.utc)
        next_sync = now + timedelta(minutes=settings.LIVE_SYNC_INTERVAL_MINUTES)
        summary = {
            "status": "completed" if not errors else ("partial" if source_results else "error"),
            "total_imported": total_imported,
            "total_duplicates": total_duplicates,
            "total_skill_links": total_skill_links,
            "ml_retrained": ml_retrained,
            "ml_metrics": ml_metrics,
            "sources": source_results,
            "errors": errors,
            "synced_at": now.isoformat(),
        }
        SYNC_STATE["last_sync_at"] = now.isoformat()
        SYNC_STATE["next_sync_at"] = next_sync.isoformat() if settings.AUTO_SYNC_LIVE_DATA else None
        SYNC_STATE["last_sync_status"] = summary["status"]
        SYNC_STATE["last_sync_summary"] = summary
        return summary
    finally:
        SYNC_STATE["is_syncing"] = False


def purge_demo_data(db: Session) -> Dict[str, Any]:
    """Veritabanındaki tüm sentetik demo ilanları ve demo içe aktarım kayıtlarını temizler."""
    demo_job_ids = [row[0] for row in db.query(Job.id).filter(Job.is_demo.is_(True)).all()]
    deleted_skills = 0
    if demo_job_ids:
        deleted_skills = (
            db.query(JobSkill)
            .filter(JobSkill.job_id.in_(demo_job_ids))
            .delete(synchronize_session=False)
        )
    deleted_jobs = db.query(Job).filter(Job.is_demo.is_(True)).delete(synchronize_session=False)
    deleted_imports = db.query(DatasetImport).filter(DatasetImport.is_demo.is_(True)).delete(synchronize_session=False)
    deleted_sources = db.query(DataSource).filter(DataSource.is_synthetic.is_(True)).delete(synchronize_session=False)
    db.commit()
    return {
        "status": "purged",
        "deleted_jobs": deleted_jobs,
        "deleted_job_skills": deleted_skills,
        "deleted_imports": deleted_imports,
        "deleted_sources": deleted_sources,
    }


def get_sync_status(db: Session) -> Dict[str, Any]:
    """Otomatik senkronizasyon durumunu ve gerçek/demo ilan sayılarını döndürür."""
    real_jobs_count = db.query(Job).filter(Job.is_demo.is_(False)).count()
    demo_jobs_count = db.query(Job).filter(Job.is_demo.is_(True)).count()
    return {
        "auto_sync_enabled": settings.AUTO_SYNC_LIVE_DATA,
        "interval_minutes": settings.LIVE_SYNC_INTERVAL_MINUTES,
        "real_jobs_count": real_jobs_count,
        "demo_jobs_count": demo_jobs_count,
        **SYNC_STATE,
    }
