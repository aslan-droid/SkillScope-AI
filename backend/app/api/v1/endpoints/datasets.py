import json
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.seed import load_synthetic_demo_dataset
from app.database.session import get_db
from app.models.entities import DatasetImport
from app.services.csv_importer import decode_csv_bytes, import_jobs_from_csv_content
from app.services.live_sync import get_sync_status, purge_demo_data, sync_live_sources

router = APIRouter()


class LiveSyncRequest(BaseModel):
    sources: Optional[List[str]] = Field(default=["lever_turkey", "remotive", "arbeitnow"])
    limit_per_source: int = Field(default=80, ge=10, le=200)
    retrain_models: bool = True


@router.get("", summary="Yüklenen tüm veri setlerini ve doğrulama durumlarını listeler")
def list_datasets(db: Session = Depends(get_db)):
    imports = db.query(DatasetImport).order_by(DatasetImport.created_at.desc()).all()
    return [
        {
            "id": imp.id,
            "filename": imp.filename,
            "source_name": imp.data_source.name if imp.data_source else "Bilinmiyor",
            "source_type": imp.data_source.source_type if imp.data_source else "CSV_UPLOAD",
            "license_name": imp.data_source.license_name if imp.data_source else "Belirtilmemiş",
            "is_demo": imp.is_demo,
            "total_rows": imp.total_rows,
            "imported_rows": imp.imported_rows,
            "duplicate_rows": imp.duplicate_rows,
            "invalid_rows": imp.invalid_rows,
            "validation_status": imp.validation_status,
            "validation_summary": imp.validation_summary,
            "created_at": imp.created_at.isoformat(),
        }
        for imp in imports
    ]


@router.post("/upload", status_code=status.HTTP_201_CREATED, summary="CSV formatında iş ilanı veri seti yükler, doğrular ve NLP ile analiz eder")
async def upload_csv_dataset(
    file: UploadFile = File(...),
    source_name: str = Form("Kullanıcı CSV Veri Seti"),
    license_name: str = Form("Kullanıcı Verisi / Açık Lisans"),
    column_mapping_json: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    filename = file.filename or "uploaded_jobs.csv"
    if not filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Yalnızca CSV (.csv) uzantılı dosyalar içe aktarılabilir.",
        )

    raw_bytes = await file.read()
    max_bytes = settings.MAX_CSV_UPLOAD_MB * 1024 * 1024
    if len(raw_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"CSV dosya boyutu en fazla {settings.MAX_CSV_UPLOAD_MB} MB olabilir.",
        )

    custom_mapping = None
    if column_mapping_json and column_mapping_json.strip():
        try:
            custom_mapping = json.loads(column_mapping_json)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Geçersiz sütun eşleştirme JSON formatı.",
            ) from exc

    csv_text = decode_csv_bytes(raw_bytes)
    try:
        result = import_jobs_from_csv_content(
            db=db,
            csv_text=csv_text,
            filename=filename,
            source_name=source_name.strip() or "Kullanıcı CSV Veri Seti",
            source_type="CSV_UPLOAD",
            license_name=license_name.strip() or "Açık Lisans",
            is_demo=False,
            custom_mapping=custom_mapping,
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/sync-status", summary="Canlı açık API senkronizasyon durumunu ve gerçek/demo ilan sayılarını döndürür")
def read_sync_status(db: Session = Depends(get_db)):
    return get_sync_status(db)


@router.post("/sync-live", summary="Remotive ve Arbeitnow açık API'lerinden gerçek iş ilanlarını hemen çeker")
def trigger_live_sync(
    payload: Optional[LiveSyncRequest] = None,
    db: Session = Depends(get_db),
):
    req = payload or LiveSyncRequest()
    return sync_live_sources(
        db=db,
        sources=req.sources,
        limit_per_source=req.limit_per_source,
        retrain_models=req.retrain_models,
    )


@router.delete("/demo-data", summary="Veritabanındaki tüm sentetik demo ilanları ve demo kayıtlarını kalıcı olarak siler")
def clear_demo_data(db: Session = Depends(get_db)):
    return purge_demo_data(db)


@router.post("/load-demo", summary="Açıkça sentetik olarak etiketlenmiş başlangıç demo veri setini yükler veya sıfırlar")
def trigger_load_demo_dataset(
    force_reload: bool = True,
    db: Session = Depends(get_db),
):
    return load_synthetic_demo_dataset(db, force_reload=force_reload)


@router.delete("/{dataset_id}", summary="Belirtilen veri setini ve bağlı iş ilanlarını siler")
def delete_dataset(dataset_id: int, db: Session = Depends(get_db)):
    imp = db.query(DatasetImport).filter(DatasetImport.id == dataset_id).first()
    if not imp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Veri seti bulunamadı.")
    db.delete(imp)
    db.commit()
    return {"status": "deleted", "dataset_id": dataset_id, "filename": imp.filename}
