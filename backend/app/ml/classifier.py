import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sqlalchemy.orm import Session

from app.models.entities import Job, ModelVersion

SUPPORTED_CATEGORIES = [
    "Yazılım geliştirme",
    "Veri analizi",
    "Yapay zekâ",
    "Siber güvenlik",
    "İş analizi",
    "Sistem ve ağ",
    "Diğer",
]


def infer_reference_category(job_title: str, description: str, sector: str = "") -> str:
    """Eğitim etiketi bulunmayan ilanlar için deterministik referans kategori belirleyici."""
    text = f"{job_title} {description} {sector}".lower().replace("İ", "i").replace("I", "ı")
    if any(k in text for k in ["siber", "cyber", "soc", "pentest", "güvenlik duvarı", "siem", "iso 27001", "zafiyet"]):
        return "Siber güvenlik"
    if any(k in text for k in ["yapay zek", "machine learning", "makine öğrenmesi", "deep learning", "derin öğrenme", "pytorch", "tensorflow", "nlp", "llm", "generative ai"]):
        return "Yapay zekâ"
    if any(k in text for k in ["veri analist", "data analyst", "power bi", "powerbi", "tableau", "iş zekası", "raporlama", "excel", "veri görselleştirme", "istatistik"]):
        return "Veri analizi"
    if any(k in text for k in ["iş analist", "business analyst", "gereksinim analizi", "bpmn", "use case", "product owner", "scrum master", "proje yönetimi"]):
        return "İş analizi"
    if any(k in text for k in ["devops", "kubernetes", "sistema", "sistem mühendis", "ağ uzman", "linux sistem", "bulut altyapı", "aws", "azure", "network"]):
        return "Sistem ve ağ"
    if any(k in text for k in ["yazılım", "developer", "geliştirici", "frontend", "backend", "full stack", "java", "c#", "typescript", "javascript", "php", "c++", "mikroservis"]):
        return "Yazılım geliştirme"
    return "Diğer"


# Başlangıç / soğuk başlatma eğitim korpusu (etiketli temel örnekler)
BOOTSTRAP_CORPUS: List[Dict[str, str]] = [
    {"text": "Backend Geliştirici Python FastAPI PostgreSQL Docker Redis REST API mikroservis yazılım geliştirme", "label": "Yazılım geliştirme"},
    {"text": "Frontend Developer React TypeScript JavaScript HTML CSS modern web arayüz geliştirme", "label": "Yazılım geliştirme"},
    {"text": "Kurumsal Java Yazılım Mühendisi Spring Boot C# .NET Core SQL Git kurumsal uygulama", "label": "Yazılım geliştirme"},
    {"text": "Full Stack Developer Node.js React TypeScript MongoDB PostgreSQL yazılım mimarisi", "label": "Yazılım geliştirme"},
    {"text": "Gömülü Yazılım Mühendisi C++ Linux gerçek zamanlı sistemler yazılım testi", "label": "Yazılım geliştirme"},
    {"text": "PHP Laravel Backend Developer MySQL Redis e-ticaret web yazılım geliştirme", "label": "Yazılım geliştirme"},
    {"text": "Veri Analisti SQL Power BI Excel veri görselleştirme dashboard raporlama istatistik KPI", "label": "Veri analizi"},
    {"text": "İş Zekası ve Raporlama Uzmanı Tableau SQL Excel veri analizi finansal raporlama", "label": "Veri analizi"},
    {"text": "Kıdemli Veri Analisti Python Pandas NumPy Statistics A/B testi veri görselleştirme", "label": "Veri analizi"},
    {"text": "Pazarlama ve Satış Veri Analisti Power BI SQL Excel müşteri segmentasyonu raporlama", "label": "Veri analizi"},
    {"text": "Finansal Veri Analisti SQL İleri Excel Power BI bütçe tahminleme istatistik", "label": "Veri analizi"},
    {"text": "Yapay Zekâ Mühendisi Python Machine Learning Deep Learning PyTorch TensorFlow model eğitimi", "label": "Yapay zekâ"},
    {"text": "NLP ve Üretken Yapay Zekâ Uzmanı Generative AI LLM RAG Python Scikit-learn doğal dil işleme", "label": "Yapay zekâ"},
    {"text": "Veri Bilimci Machine Learning Scikit-learn Python Pandas istatistiksel modelleme tahminleme", "label": "Yapay zekâ"},
    {"text": "Bilgisayarlı Görü ve Derin Öğrenme Mühendisi PyTorch TensorFlow Deep Learning C++ Python", "label": "Yapay zekâ"},
    {"text": "Makine Öğrenmesi Mühendisi MLOps Docker Python Scikit-learn model değerlendirme", "label": "Yapay zekâ"},
    {"text": "Siber Güvenlik Uzmanı Linux ağ güvenliği SIEM SOC sızma testi pentest zafiyet analizi", "label": "Siber güvenlik"},
    {"text": "SOC Analisti Siber Güvenlik olay müdahale güvenlik duvarı log analizi Linux Python", "label": "Siber güvenlik"},
    {"text": "Uygulama Güvenliği Mühendisi DevSecOps Docker Linux siber güvenlik kaynak kod analizi", "label": "Siber güvenlik"},
    {"text": "Bilgi Güvenliği ve Siber Savunma Uzmanı ISO 27001 ağ güvenliği sızma testi", "label": "Siber güvenlik"},
    {"text": "Teknik İş Analisti Business Analysis Agile Scrum gereksinim analizi SQL süreç modelleme", "label": "İş analizi"},
    {"text": "Kıdemli İş Analisti ve Ürün Sahibi Product Owner Scrum Jira iletişim proje yönetimi", "label": "İş analizi"},
    {"text": "BT İş Analisti BPMN use case müşteri gereksinimleri Agile Scrum raporlama", "label": "İş analizi"},
    {"text": "Dijital Dönüşüm Proje Yöneticisi ve İş Analisti Project Management Business Analysis Agile", "label": "İş analizi"},
    {"text": "DevOps ve Bulut Sistem Mühendisi Docker Kubernetes Linux AWS Azure CI/CD otomasyon", "label": "Sistem ve ağ"},
    {"text": "Linux Sistem ve Ağ Yöneticisi Linux sunucu yönetimi network bulut altyapı güvenlik", "label": "Sistem ve ağ"},
    {"text": "Bulut Altyapı Mühendisi AWS Azure Kubernetes Docker yüksek erişilebilirlik sistem", "label": "Sistem ve ağ"},
    {"text": "Site Reliability Engineer SRE Kubernetes Linux Docker izleme ve sistem yönetimi", "label": "Sistem ve ağ"},
    {"text": "Genel Teknoloji Danışmanı müşteri iletişimi teknik destek operasyon dokümantasyon", "label": "Diğer"},
    {"text": "Teknoloji Eğitim Koordinatörü sunum iletişim içerik hazırlama organizasyon", "label": "Diğer"},
]


class JobClassifierService:
    """
    TF-IDF ve Lojistik Regresyon kullanarak iş ilanlarını 7 ana kategoriye ayıran,
    gerçek verilerle eğitilen, metriklerini (Accuracy, Precision, Recall, F1)
    veritabanına ve model deposuna kaydeden ML servisi.
    """

    MODEL_NAME = "skillscope_job_classifier"
    VERSION = "1.0.0"

    def __init__(self, artifact_dir: Optional[str] = None):
        base_dir = Path(artifact_dir) if artifact_dir else Path(__file__).resolve().parents[3] / "ml" / "models"
        base_dir.mkdir(parents=True, exist_ok=True)
        self.artifact_path = base_dir / f"{self.MODEL_NAME}_v{self.VERSION}.joblib"
        self.pipeline: Optional[Pipeline] = None

    def train_and_evaluate(self, db: Session) -> Dict[str, Any]:
        jobs = db.query(Job).all()
        texts: List[str] = []
        labels: List[str] = []

        trained_on_demo = False
        for j in jobs:
            if j.is_demo:
                trained_on_demo = True
            combined = f"{j.job_title} {j.sector or ''} {j.description}"
            label = j.predicted_category if j.predicted_category in SUPPORTED_CATEGORIES else infer_reference_category(j.job_title, j.description, j.sector or "")
            texts.append(combined)
            labels.append(label)

        # Her kategoriden yeterli örnek bulunması için temel korpus ile destekle
        for item in BOOTSTRAP_CORPUS:
            texts.append(item["text"])
            labels.append(item["label"])

        is_experimental = len(jobs) < 50

        X_train, X_test, y_train, y_test = train_test_split(
            texts,
            labels,
            test_size=0.25,
            random_state=42,
            stratify=labels if len(set(labels)) > 1 and min(labels.count(c) for c in set(labels)) >= 2 else None,
        )

        pipeline = Pipeline(
            [
                (
                    "tfidf",
                    TfidfVectorizer(
                        ngram_range=(1, 2),
                        max_features=3500,
                        sublinear_tf=True,
                    ),
                ),
                (
                    "clf",
                    LogisticRegression(
                        max_iter=1000,
                        C=2.0,
                        class_weight="balanced",
                        random_state=42,
                    ),
                ),
            ]
        )

        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)

        acc = float(round(accuracy_score(y_test, y_pred), 4))
        prec = float(round(precision_score(y_test, y_pred, average="weighted", zero_division=0), 4))
        rec = float(round(recall_score(y_test, y_pred, average="weighted", zero_division=0), 4))
        f1 = float(round(f1_score(y_test, y_pred, average="weighted", zero_division=0), 4))

        self.pipeline = pipeline
        joblib.dump(pipeline, self.artifact_path)

        # Gerçek vs Tahmin örnek karşılaştırma tablosu
        comparison_records = []
        for idx in range(min(15, len(X_test))):
            snippet = X_test[idx][:90] + ("..." if len(X_test[idx]) > 90 else "")
            comparison_records.append(
                {
                    "sample": snippet,
                    "actual": y_test[idx],
                    "predicted": str(y_pred[idx]),
                    "correct": bool(y_test[idx] == y_pred[idx]),
                }
            )

        # İlanların predicted_category alanlarını güncelle
        if jobs:
            job_texts = [f"{j.job_title} {j.sector or ''} {j.description}" for j in jobs]
            predicted_labels = pipeline.predict(job_texts)
            for j, pred_label in zip(jobs, predicted_labels):
                j.predicted_category = str(pred_label)

        metrics = {
            "accuracy": acc,
            "precision": prec,
            "recall": rec,
            "f1_score": f1,
            "supported_categories": SUPPORTED_CATEGORIES,
        }

        model_record = ModelVersion(
            model_name=self.MODEL_NAME,
            model_type="JOB_CLASSIFIER",
            version=self.VERSION,
            algorithm="TF-IDF (1-2 ngram) + LogisticRegression (Balanced)",
            training_samples=len(X_train),
            test_samples=len(X_test),
            metrics=metrics,
            comparison_data=comparison_records,
            artifact_path=str(self.artifact_path),
            is_experimental=is_experimental,
            trained_on_demo=trained_on_demo,
            notes=(
                "Deneysel mod: Gerçek ilan sayısı 50'nin altında olduğu için sonuçlar deneysel olarak etiketlenmiştir."
                if is_experimental
                else "Doğrulanmış eğitim ve test ayrımı ile değerlendirildi."
            ),
            trained_at=datetime.now(timezone.utc),
        )
        db.add(model_record)
        db.commit()
        db.refresh(model_record)

        return {
            "model_id": model_record.id,
            "model_name": model_record.model_name,
            "version": model_record.version,
            "metrics": metrics,
            "training_samples": len(X_train),
            "test_samples": len(X_test),
            "is_experimental": is_experimental,
            "trained_on_demo": trained_on_demo,
            "comparison_data": comparison_records,
        }

    def load_or_train(self, db: Session) -> Pipeline:
        if self.pipeline is not None:
            return self.pipeline
        if self.artifact_path.exists():
            try:
                self.pipeline = joblib.load(self.artifact_path)
                return self.pipeline
            except Exception:
                pass
        self.train_and_evaluate(db)
        return self.pipeline  # type: ignore[return-value]

    def predict_category(self, db: Session, title: str, description: str, sector: str = "") -> Dict[str, Any]:
        pipeline = self.load_or_train(db)
        combined = f"{title} {sector} {description}"
        pred = str(pipeline.predict([combined])[0])
        probs = pipeline.predict_proba([combined])[0]
        classes = list(pipeline.classes_)
        confidence = float(round(max(probs), 4))
        top_probabilities = {
            str(cls_name): float(round(prob, 4))
            for cls_name, prob in sorted(zip(classes, probs), key=lambda x: x[1], reverse=True)[:4]
        }
        total_jobs = db.query(Job).count()
        return {
            "predicted_category": pred,
            "confidence": confidence,
            "probabilities": top_probabilities,
            "is_experimental": total_jobs < 50,
        }
