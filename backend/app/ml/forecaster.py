from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sqlalchemy import func
from sqlalchemy.orm import Session
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from app.models.entities import Job, JobSkill, ModelVersion, Skill


class SkillForecasterService:
    """
    Zaman serisi verisi bulunan beceriler için aylık talep sayısını çıkaran,
    zamana göre eğitim ve test verisini ayıran, MAE ve RMSE metriklerini hesaplayan
    ve gelecek dönemler için tahmin + güven aralığı üreten servis.
    """

    MODEL_NAME = "skillscope_skill_forecaster"
    VERSION = "1.0.0"
    MIN_MONTHS_REQUIRED = 6
    MIN_TOTAL_OBSERVATIONS = 12

    def __init__(self, artifact_dir: Optional[str] = None):
        base_dir = Path(artifact_dir) if artifact_dir else Path(__file__).resolve().parents[3] / "ml" / "models"
        base_dir.mkdir(parents=True, exist_ok=True)
        self.artifact_dir = base_dir

    def _get_monthly_series(self, db: Session, skill_slug_or_name: str, include_demo: bool = True) -> Dict[str, Any]:
        skill = (
            db.query(Skill)
            .filter(
                (func.lower(Skill.slug) == skill_slug_or_name.lower())
                | (func.lower(Skill.name) == skill_slug_or_name.lower())
            )
            .first()
        )
        if not skill:
            return {"skill": None, "series": pd.Series(dtype=float), "has_demo": False}

        query = (
            db.query(Job.posted_date, Job.is_demo)
            .join(JobSkill, Job.id == JobSkill.job_id)
            .filter(JobSkill.skill_id == skill.id)
        )
        if not include_demo:
            query = query.filter(Job.is_demo.is_(False))

        rows = query.all()
        if not rows:
            return {"skill": skill, "series": pd.Series(dtype=float), "has_demo": False}

        has_demo = any(bool(r[1]) for r in rows)
        dates = pd.to_datetime([r[0] for r in rows])
        df = pd.DataFrame({"month": dates.to_period("M")})
        monthly_counts = df.groupby("month").size()

        full_period_index = pd.period_range(start=monthly_counts.index.min(), end=monthly_counts.index.max(), freq="M")
        monthly_counts = monthly_counts.reindex(full_period_index, fill_value=0).astype(float)
        return {"skill": skill, "series": monthly_counts, "has_demo": has_demo}

    @staticmethod
    def _fit_and_predict(train_values: np.ndarray, steps: int) -> np.ndarray:
        """
        Yeterli nokta varsa Holt Exponential Smoothing (trend modelli),
        daha kısa serilerde sönümlü doğrusal trend regresyonu uygular.
        """
        if len(train_values) >= 5 and np.std(train_values) > 0:
            try:
                model = ExponentialSmoothing(
                    train_values,
                    trend="add",
                    damped_trend=True,
                    seasonal=None,
                    initialization_method="estimated",
                )
                fitted = model.fit(optimized=True)
                preds = fitted.forecast(steps)
                return np.maximum(0.0, np.asarray(preds, dtype=float))
            except Exception:
                pass

        x = np.arange(len(train_values), dtype=float)
        slope, intercept = np.polyfit(x, train_values, 1)
        future_x = np.arange(len(train_values), len(train_values) + steps, dtype=float)
        preds = intercept + slope * future_x
        return np.maximum(0.0, preds)

    def forecast_skill_demand(
        self,
        db: Session,
        skill_identifier: str,
        horizon_months: int = 3,
        include_demo: bool = True,
        persist_model_record: bool = False,
    ) -> Dict[str, Any]:
        data = self._get_monthly_series(db, skill_identifier, include_demo=include_demo)
        skill = data["skill"]
        series: pd.Series = data["series"]
        has_demo: bool = data["has_demo"]

        if not skill:
            return {
                "forecast_available": False,
                "skill_name": skill_identifier,
                "reason": f"'{skill_identifier}' becerisi sözlükte bulunamadı.",
                "history": [],
                "forecast": [],
                "metrics": None,
            }

        num_months = len(series)
        total_obs = int(series.sum()) if num_months > 0 else 0

        if num_months < self.MIN_MONTHS_REQUIRED or total_obs < self.MIN_TOTAL_OBSERVATIONS:
            return {
                "forecast_available": False,
                "skill_name": skill.name,
                "skill_slug": skill.slug,
                "reason": (
                    f"Güvenilir zaman serisi tahmini için en az {self.MIN_MONTHS_REQUIRED} aylık veri dönemi ve "
                    f"en az {self.MIN_TOTAL_OBSERVATIONS} ilan gözlemi gereklidir. "
                    f"Mevcut veri: {num_months} ay, toplam {total_obs} ilan."
                ),
                "data_period": (
                    f"{series.index.min()} - {series.index.max()}" if num_months > 0 else "Veri yok"
                ),
                "includes_demo_data": has_demo,
                "history": [
                    {"period": str(idx), "actual": int(val)}
                    for idx, val in series.items()
                ],
                "forecast": [],
                "comparison": [],
                "metrics": None,
            }

        values = series.values.astype(float)
        periods = [str(p) for p in series.index]

        # Zamana göre eğitim ve test ayrımı (son %25 veya en az 2 ay test)
        test_size = max(2, int(round(num_months * 0.25)))
        train_size = num_months - test_size

        train_vals = values[:train_size]
        test_vals = values[train_size:]
        test_periods = periods[train_size:]

        test_preds = self._fit_and_predict(train_vals, steps=test_size)

        mae = float(round(mean_absolute_error(test_vals, test_preds), 3))
        rmse = float(round(np.sqrt(mean_squared_error(test_vals, test_preds)), 3))

        # Tüm geçmiş seri üzerinden gelecek dönem tahmini
        future_preds = self._fit_and_predict(values, steps=horizon_months)
        last_period = series.index.max()
        future_periods = [str(last_period + i) for i in range(1, horizon_months + 1)]

        # Tahmin aralığı (residual std / RMSE tabanlı %90 güven bandı)
        band_half_width = max(1.0, 1.645 * (rmse if rmse > 0 else np.std(values) * 0.25))

        history_points = []
        for idx, p in enumerate(periods):
            point: Dict[str, Any] = {
                "period": p,
                "actual": int(round(values[idx])),
                "split": "train" if idx < train_size else "test",
            }
            if idx >= train_size:
                pred_val = float(round(test_preds[idx - train_size], 2))
                point["test_predicted"] = pred_val
            history_points.append(point)

        comparison_records = [
            {
                "period": test_periods[i],
                "actual": int(round(test_vals[i])),
                "predicted": float(round(test_preds[i], 2)),
                "error": float(round(abs(test_vals[i] - test_preds[i]), 2)),
            }
            for i in range(test_size)
        ]

        forecast_points = []
        for i in range(horizon_months):
            val = float(round(future_preds[i], 2))
            horizon_scale = 1.0 + (0.15 * i)
            lower = float(round(max(0.0, val - band_half_width * horizon_scale), 2))
            upper = float(round(val + band_half_width * horizon_scale, 2))
            forecast_points.append(
                {
                    "period": future_periods[i],
                    "predicted": val,
                    "lower_bound": lower,
                    "upper_bound": upper,
                }
            )

        metrics = {
            "mae": mae,
            "rmse": rmse,
            "train_months": train_size,
            "test_months": test_size,
            "total_observations": total_obs,
        }

        if persist_model_record:
            artifact_file = self.artifact_dir / f"{self.MODEL_NAME}_{skill.slug}_v{self.VERSION}.joblib"
            joblib.dump(
                {
                    "skill": skill.name,
                    "periods": periods,
                    "values": values.tolist(),
                    "metrics": metrics,
                    "forecast": forecast_points,
                },
                artifact_file,
            )
            model_record = ModelVersion(
                model_name=f"{self.MODEL_NAME}:{skill.slug}",
                model_type="SKILL_FORECASTER",
                version=self.VERSION,
                algorithm="Holt Damped Trend Exponential Smoothing + Temporal Split",
                training_samples=train_size,
                test_samples=test_size,
                metrics=metrics,
                comparison_data=comparison_records,
                artifact_path=str(artifact_file),
                is_experimental=has_demo,
                trained_on_demo=has_demo,
                notes=(
                    "Sentetik demo verisi içerdiğinden tahminler sistem yeteneklerini gösterme amaçlıdır."
                    if has_demo
                    else "Gerçek zaman serisi verisi üzerinde zamana dayalı eğitim/test ayrımı ile değerlendirildi."
                ),
                trained_at=datetime.now(timezone.utc),
            )
            db.add(model_record)
            db.commit()

        return {
            "forecast_available": True,
            "skill_name": skill.name,
            "skill_slug": skill.slug,
            "data_period": f"{periods[0]} — {periods[-1]}",
            "includes_demo_data": has_demo,
            "disclaimer": (
                "Bu tahmin sentetik demo veri setini içermektedir; gerçek piyasa garantisi olarak kullanılmamalıdır."
                if has_demo
                else "Zamana dayalı eğitim/test ayrımıyla doğrulanmış istatistiksel trend tahmini."
            ),
            "metrics": metrics,
            "history": history_points,
            "comparison": comparison_records,
            "forecast": forecast_points,
        }
