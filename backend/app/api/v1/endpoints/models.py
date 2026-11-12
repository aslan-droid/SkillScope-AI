from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.ml.classifier import JobClassifierService
from app.ml.forecaster import SkillForecasterService
from app.models.entities import ModelVersion
from app.schemas.api_schemas import ClassifyJobTextRequest

router = APIRouter()


@router.get("", summary="Eğitilen tüm makine öğrenmesi modellerini, versiyonlarını ve test metriklerini listeler")
def list_model_versions(db: Session = Depends(get_db)):
    models = db.query(ModelVersion).order_by(ModelVersion.trained_at.desc()).limit(25).all()
    return [
        {
            "id": m.id,
            "model_name": m.model_name,
            "model_type": m.model_type,
            "version": m.version,
            "algorithm": m.algorithm,
            "training_samples": m.training_samples,
            "test_samples": m.test_samples,
            "metrics": m.metrics,
            "comparison_data": m.comparison_data,
            "is_experimental": m.is_experimental,
            "trained_on_demo": m.trained_on_demo,
            "notes": m.notes,
            "trained_at": m.trained_at.isoformat(),
        }
        for m in models
    ]


@router.post("/train", summary="İlan sınıflandırma ve beceri talep tahmin modellerini güncel verilerle yeniden eğitir")
def train_all_models(db: Session = Depends(get_db)):
    clf_service = JobClassifierService()
    clf_result = clf_service.train_and_evaluate(db)

    forecaster = SkillForecasterService()
    forecast_results = {}
    for sk in ("sql", "python", "power-bi", "docker", "typescript"):
        forecast_results[sk] = forecaster.forecast_skill_demand(
            db=db,
            skill_identifier=sk,
            horizon_months=3,
            include_demo=True,
            persist_model_record=True,
        )

    return {
        "status": "trained",
        "classifier": clf_result,
        "forecasters": forecast_results,
    }


@router.get("/forecast/{skill_identifier}", summary="Belirli bir beceri için zaman serisi talep tahmini, MAE/RMSE ve güven aralığı döner")
def get_skill_forecast(
    skill_identifier: str,
    horizon_months: int = Query(3, ge=1, le=6),
    include_demo: bool = Query(True),
    db: Session = Depends(get_db),
):
    forecaster = SkillForecasterService()
    return forecaster.forecast_skill_demand(
        db=db,
        skill_identifier=skill_identifier,
        horizon_months=horizon_months,
        include_demo=include_demo,
        persist_model_record=False,
    )


@router.post("/classify", summary="Verilen iş ilanı başlığı ve açıklamasını ML modeliyle sınıflandırır")
def classify_job_text(payload: ClassifyJobTextRequest, db: Session = Depends(get_db)):
    clf_service = JobClassifierService()
    return clf_service.predict_category(
        db=db,
        title=payload.job_title,
        description=payload.description,
        sector=payload.sector,
    )
