from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import get_db
from app.models.entities import CVAnalysis
from app.services.cv_and_career import analyze_cv_and_match, extract_text_from_pdf_bytes

router = APIRouter()


@router.post("/analyze", summary="PDF formatındaki CV'yi bellekte analiz eder ve hedef pozisyonla karşılaştırır")
async def analyze_uploaded_cv(
    file: UploadFile = File(...),
    target_role: str = Form("Veri Analisti"),
    save_record: bool = Form(True),
    db: Session = Depends(get_db),
):
    filename = file.filename or "cv.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Yalnızca PDF (.pdf) formatındaki CV dosyaları kabul edilmektedir.",
        )

    raw_bytes = await file.read()
    max_bytes = settings.MAX_CV_UPLOAD_MB * 1024 * 1024
    if len(raw_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"CV dosya boyutu en fazla {settings.MAX_CV_UPLOAD_MB} MB olabilir.",
        )

    try:
        cv_text = extract_text_from_pdf_bytes(raw_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return analyze_cv_and_match(
        db=db,
        cv_text=cv_text,
        target_role=target_role,
        filename=filename,
        save_record=save_record,
    )


@router.get("/history", summary="Kaydedilmiş CV analiz özetlerini listeler")
def list_cv_analyses(db: Session = Depends(get_db)):
    records = db.query(CVAnalysis).order_by(CVAnalysis.created_at.desc()).limit(10).all()
    return [
        {
            "id": r.id,
            "filename": r.filename,
            "target_role": r.target_role,
            "extracted_skills": r.extracted_skills,
            "skill_alignment_percentage": r.match_score,
            "matched_skills": r.matched_skills,
            "missing_skills": r.missing_skills,
            "created_at": r.created_at.isoformat(),
        }
        for r in records
    ]


@router.delete("/{analysis_id}", summary="Kullanıcının CV analiz kaydını kalıcı olarak siler")
def delete_cv_analysis(analysis_id: int, db: Session = Depends(get_db)):
    record = db.query(CVAnalysis).filter(CVAnalysis.id == analysis_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CV analiz kaydı bulunamadı.")
    db.delete(record)
    db.commit()
    return {"status": "deleted", "analysis_id": analysis_id, "message": "CV analiz kaydınız kalıcı olarak silindi."}
