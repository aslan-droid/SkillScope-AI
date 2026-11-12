import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from app.database.session import SessionLocal, Base, engine
from app.database.seed import load_synthetic_demo_dataset
from app.ml.classifier import JobClassifierService
from app.ml.forecaster import SkillForecasterService


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        load_synthetic_demo_dataset(db, force_reload=False)
        clf = JobClassifierService()
        clf_metrics = clf.train_and_evaluate(db)
        print("İlan Sınıflandırma Modeli Eğitildi:", clf_metrics["metrics"])

        forecaster = SkillForecasterService()
        for skill_slug in ("sql", "python", "power-bi", "docker"):
            res = forecaster.forecast_skill_demand(db, skill_slug, horizon_months=3, persist_model_record=True)
            print(f"Beceri Talep Tahmini ({skill_slug}):", res.get("metrics"))
    finally:
        db.close()


if __name__ == "__main__":
    main()
