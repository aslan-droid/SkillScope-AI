import csv
import io
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.core.security import compute_job_fingerprint
from app.ml.classifier import infer_reference_category
from app.models.entities import Category, Company, DatasetImport, DataSource, Job, JobSkill, Skill
from app.nlp.extractor import SkillExtractor, normalize_role_title

# Farklı CSV dosyalarındaki sütun adlarını standart şemaya eşleştiren sözlük
COLUMN_ALIASES: Dict[str, List[str]] = {
    "job_title": ["job_title", "title", "ilan_basligi", "pozisyon", "position", "role", "baslik", "meslek"],
    "company": ["company", "company_name", "sirket", "firma", "employer", "kurum"],
    "location": ["location", "city", "sehir", "konum", "il", "lokasyon"],
    "description": ["description", "job_description", "aciklama", "ilan_aciklamasi", "nitelikler", "detay", "content"],
    "employment_type": ["employment_type", "calisma_tipi", "istihdam_turu", "contract_type", "type"],
    "salary_min": ["salary_min", "min_salary", "alt_maas", "maas_min", "minimum_maas"],
    "salary_max": ["salary_max", "max_salary", "ust_maas", "maas_max", "maksimum_maas"],
    "currency": ["currency", "para_birimi", "doviz"],
    "remote_type": ["remote_type", "work_mode", "calisma_sekli", "calisma_modeli", "remote"],
    "posted_date": ["posted_date", "date", "yayin_tarihi", "tarih", "published_at", "created_at"],
    "source_url": ["source_url", "url", "link", "ilan_linki"],
    "source_name": ["source_name", "source", "kaynak", "veri_kaynagi"],
    "sector": ["sector", "industry", "sektor", "alan"],
}

REQUIRED_STANDARD_COLUMNS = ["job_title", "description"]


def decode_csv_bytes(raw_bytes: bytes) -> str:
    """UTF-8, UTF-8-BOM ve Türkçe Windows-1254 (cp1254) karakter kodlamalarını güvenle çözümler."""
    for enc in ("utf-8-sig", "utf-8", "cp1254", "iso-8859-9", "latin-1"):
        try:
            return raw_bytes.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw_bytes.decode("utf-8", errors="replace")


def resolve_column_mapping(csv_headers: List[str], custom_mapping: Optional[Dict[str, str]] = None) -> Tuple[Dict[str, str], List[str]]:
    """
    CSV başlıklarını standart sütunlara eşleştirir.
    Döndürür: (standard_col -> csv_header eşleşmesi, eksik zorunlu sütunlar)
    """
    normalized_headers = {h.strip().lower(): h for h in csv_headers if h and h.strip()}
    resolved: Dict[str, str] = {}

    if custom_mapping:
        for std_col, user_col in custom_mapping.items():
            if user_col in csv_headers:
                resolved[std_col] = user_col
            elif user_col.strip().lower() in normalized_headers:
                resolved[std_col] = normalized_headers[user_col.strip().lower()]

    for std_col, aliases in COLUMN_ALIASES.items():
        if std_col in resolved:
            continue
        for alias in aliases:
            if alias.lower() in normalized_headers:
                resolved[std_col] = normalized_headers[alias.lower()]
                break

    missing_required = [req for req in REQUIRED_STANDARD_COLUMNS if req not in resolved]
    return resolved, missing_required


def _parse_date(raw_val: Optional[str]) -> date:
    if not raw_val or not str(raw_val).strip():
        return date.today()
    s = str(raw_val).strip()[:10]
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return date.today()


def _parse_float(raw_val: Optional[str]) -> Optional[float]:
    if raw_val is None or str(raw_val).strip() == "":
        return None
    cleaned = str(raw_val).strip().replace(".", "").replace(",", ".") if "," in str(raw_val) and "." in str(raw_val) else str(raw_val).strip().replace(",", ".")
    try:
        val = float(cleaned)
        return val if val > 0 else None
    except ValueError:
        return None


def _normalize_remote_type(raw_val: Optional[str], description: str = "") -> str:
    combined = f"{raw_val or ''} {description[:200]}".lower()
    if any(k in combined for k in ["uzaktan", "remote", "evden", "home office", "tamamen uzaktan"]):
        return "Uzaktan"
    if any(k in combined for k in ["hibrit", "hybrid", "karma"]):
        return "Hibrit"
    if any(k in combined for k in ["ofis", "onsite", "on-site", "işyerinde", "isyeri"]):
        return "Ofisten"
    return "Hibrit"


def import_jobs_from_csv_content(
    db: Session,
    csv_text: str,
    filename: str,
    source_name: str = "Kullanıcı CSV Yüklemesi",
    source_type: str = "CSV_UPLOAD",
    license_name: str = "Kullanıcı Tarafından Sağlanan Veri",
    is_demo: bool = False,
    custom_mapping: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    CSV metnini doğrular, sütunları eşleştirir, mükerrer ilanları filtreler,
    NLP beceri çıkarımı ve kategori sınıflandırmasını çalıştırarak PostgreSQL'e kaydeder.
    """
    reader = csv.DictReader(io.StringIO(csv_text))
    headers = list(reader.fieldnames or [])
    if not headers:
        raise ValueError("CSV dosyasında geçerli sütun başlığı bulunamadı.")

    mapping, missing_required = resolve_column_mapping(headers, custom_mapping)
    if missing_required:
        raise ValueError(
            f"Zorunlu sütunlar eşleştirilemedi: {', '.join(missing_required)}. "
            f"Mevcut sütunlar: {', '.join(headers)}. "
            "Lütfen 'job_title' (veya 'ilan_basligi') ve 'description' (veya 'aciklama') sütunlarının bulunduğundan emin olun."
        )

    records: List[Dict[str, Any]] = []
    for row in reader:
        records.append(
            {
                "job_title": row.get(mapping["job_title"]) or "",
                "description": row.get(mapping["description"]) or "",
                "company": row.get(mapping.get("company", ""), ""),
                "location": row.get(mapping.get("location", ""), ""),
                "sector": row.get(mapping.get("sector", ""), ""),
                "employment_type": row.get(mapping.get("employment_type", ""), ""),
                "remote_type": row.get(mapping.get("remote_type", "")),
                "salary_min": row.get(mapping.get("salary_min", "")),
                "salary_max": row.get(mapping.get("salary_max", "")),
                "currency": row.get(mapping.get("currency", ""), ""),
                "posted_date": row.get(mapping.get("posted_date", "")),
                "source_url": row.get(mapping.get("source_url", ""), ""),
                "source_name": row.get(mapping.get("source_name", ""), "") or source_name,
            }
        )

    optional_columns = [col for col in COLUMN_ALIASES.keys() if col not in mapping]
    return ingest_job_records(
        db=db,
        records=records,
        filename=filename,
        source_name=source_name,
        source_type=source_type,
        license_name=license_name,
        is_demo=is_demo,
        mapped_columns=mapping,
        missing_optional_columns=optional_columns,
    )


def ingest_job_records(
    db: Session,
    records: List[Dict[str, Any]],
    filename: str,
    source_name: str,
    source_type: str = "PUBLIC_API",
    license_name: str = "Açık API / Kamu Verisi",
    is_demo: bool = False,
    mapped_columns: Optional[Dict[str, str]] = None,
    missing_optional_columns: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Normalize edilmiş iş ilanı kayıtlarını doğrular, mükerrerleri eler, NLP ile etiketler ve DB'ye yazar."""
    data_source = db.query(DataSource).filter(DataSource.name == source_name).first()
    if not data_source:
        data_source = DataSource(
            name=source_name,
            source_type=source_type,
            license_name=license_name,
            is_synthetic=is_demo,
            description=(
                "Sistem özelliklerini göstermek için oluşturulmuş açık etiketli sentetik demo veri kaynağı."
                if is_demo
                else "Kullanıcı veya açık veri seti/API üzerinden içe aktarılan veri kaynağı."
            ),
        )
        db.add(data_source)
        db.flush()

    dataset_import = DatasetImport(
        data_source_id=data_source.id,
        filename=filename,
        is_demo=is_demo,
        validation_status="PROCESSING",
    )
    db.add(dataset_import)
    db.flush()

    extractor = SkillExtractor.from_db(db)
    skill_map: Dict[str, Skill] = {s.slug: s for s in db.query(Skill).all()}
    company_cache: Dict[str, Company] = {c.name.lower(): c for c in db.query(Company).all()}
    category_cache: Dict[str, Category] = {c.name: c for c in db.query(Category).all()}
    existing_hashes = {r[0] for r in db.query(Job.content_hash).all()}

    total_rows = 0
    imported_rows = 0
    duplicate_rows = 0
    invalid_rows = 0
    extracted_skill_links = 0
    row_errors: List[str] = []

    for idx, row in enumerate(records, start=1):
        total_rows += 1
        raw_title = str(row.get("job_title") or "").strip()
        raw_desc = str(row.get("description") or "").strip()

        if len(raw_title) < 2 or len(raw_desc) < 10:
            invalid_rows += 1
            if len(row_errors) < 10:
                row_errors.append(f"Satır {idx}: Başlık çok kısa veya açıklama 10 karakterden az.")
            continue

        raw_company = str(row.get("company") or "Belirtilmemiş").strip() or "Belirtilmemiş"
        raw_location = str(row.get("location") or "Global / Uzaktan").strip() or "Global / Uzaktan"
        raw_sector = str(row.get("sector") or "Teknoloji").strip() or "Teknoloji"
        raw_emp = str(row.get("employment_type") or "Tam Zamanlı").strip() or "Tam Zamanlı"
        raw_remote = _normalize_remote_type(row.get("remote_type"), raw_desc)
        salary_min = _parse_float(row.get("salary_min"))
        salary_max = _parse_float(row.get("salary_max"))
        if salary_min and salary_max and salary_min > salary_max:
            salary_min, salary_max = salary_max, salary_min

        currency = str(row.get("currency") or "TRY").strip().upper() or "TRY"
        posted_raw = row.get("posted_date")
        posted_dt = posted_raw if isinstance(posted_raw, datetime) else _parse_date(posted_raw)
        source_url = str(row.get("source_url") or "").strip() or None
        row_source = str(row.get("source_name") or source_name).strip() or source_name

        content_hash = compute_job_fingerprint(raw_title, raw_company, raw_location, raw_desc)
        if content_hash in existing_hashes:
            duplicate_rows += 1
            continue
        existing_hashes.add(content_hash)

        comp_obj = company_cache.get(raw_company.lower())
        if not comp_obj:
            comp_obj = Company(name=raw_company, sector=raw_sector, city=raw_location)
            db.add(comp_obj)
            db.flush()
            company_cache[raw_company.lower()] = comp_obj

        pred_cat_name = infer_reference_category(raw_title, raw_desc, raw_sector)
        cat_obj = category_cache.get(pred_cat_name)
        if not cat_obj:
            slug = (
                pred_cat_name.lower()
                .replace(" ", "-")
                .replace("ı", "i")
                .replace("ğ", "g")
                .replace("ü", "u")
                .replace("ş", "s")
                .replace("ö", "o")
                .replace("ç", "c")
                .replace("â", "a")
            )
            cat_obj = Category(name=pred_cat_name, slug=slug, description=f"{pred_cat_name} iş ilanları kategorisi")
            db.add(cat_obj)
            db.flush()
            category_cache[pred_cat_name] = cat_obj

        job_obj = Job(
            job_title=raw_title,
            normalized_role=normalize_role_title(raw_title),
            company_id=comp_obj.id,
            company_name=raw_company,
            category_id=cat_obj.id,
            dataset_import_id=dataset_import.id,
            location=raw_location,
            sector=raw_sector,
            description=raw_desc,
            employment_type=raw_emp,
            remote_type=raw_remote,
            salary_min=salary_min,
            salary_max=salary_max,
            currency=currency,
            posted_date=posted_dt,
            source_url=source_url,
            source_name=row_source,
            content_hash=content_hash,
            is_demo=is_demo,
            predicted_category=pred_cat_name,
        )
        db.add(job_obj)
        db.flush()

        # NLP ile beceri çıkarımı
        combined_text = f"{raw_title}\n{raw_desc}"
        found_skills = extractor.extract_skills(combined_text)
        for sk in found_skills:
            skill_entity = skill_map.get(sk["slug"])
            if skill_entity:
                db.add(
                    JobSkill(
                        job_id=job_obj.id,
                        skill_id=skill_entity.id,
                        matched_term=sk.get("matched_term"),
                        confidence=float(sk.get("confidence", 1.0)),
                    )
                )
                extracted_skill_links += 1

        imported_rows += 1

    if imported_rows > 0 and invalid_rows == 0:
        status = "VALIDATED"
    elif imported_rows == 0 and duplicate_rows > 0 and invalid_rows == 0:
        status = "VALIDATED"
    elif imported_rows > 0:
        status = "PARTIAL"
    else:
        status = "FAILED"

    summary_info = {
        "mapped_columns": mapped_columns or {},
        "missing_optional_columns": missing_optional_columns or [],
        "extracted_skill_links": extracted_skill_links,
        "row_errors": row_errors,
    }

    dataset_import.total_rows = total_rows
    dataset_import.imported_rows = imported_rows
    dataset_import.duplicate_rows = duplicate_rows
    dataset_import.invalid_rows = invalid_rows
    dataset_import.validation_status = status
    dataset_import.validation_summary = summary_info

    db.commit()
    db.refresh(dataset_import)

    return {
        "dataset_id": dataset_import.id,
        "filename": dataset_import.filename,
        "source_name": data_source.name,
        "is_demo": is_demo,
        "total_rows": total_rows,
        "imported_rows": imported_rows,
        "duplicate_rows": duplicate_rows,
        "invalid_rows": invalid_rows,
        "extracted_skill_links": extracted_skill_links,
        "validation_status": status,
        "validation_summary": summary_info,
        "created_at": dataset_import.created_at.isoformat(),
    }
