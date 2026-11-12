import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from app.database.session import SessionLocal
from app.models.entities import ModelVersion


def export_evaluation_report() -> dict:
    db = SessionLocal()
    try:
        versions = db.query(ModelVersion).order_by(ModelVersion.trained_at.desc()).all()
        report = {
            "total_models_evaluated": len(versions),
            "models": [
                {
                    "model_name": m.model_name,
                    "model_type": m.model_type,
                    "version": m.version,
                    "algorithm": m.algorithm,
                    "metrics": m.metrics,
                    "is_experimental": m.is_experimental,
                    "trained_on_demo": m.trained_on_demo,
                    "trained_at": m.trained_at.isoformat(),
                }
                for m in versions
            ],
        }
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return report
    finally:
        db.close()


if __name__ == "__main__":
    export_evaluation_report()
