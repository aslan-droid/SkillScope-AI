# SkillScope AI — Teknik Mimari Dokümanı (`docs/architecture.md`)

## 1. Genel Bakış

SkillScope AI, iş piyasasındaki dağınık iş ilanı metinlerini anlamlandıran, aranan becerileri NLP ile çıkaran, zaman serisi talep tahmini ve ilan sınıflandırması yapan, PDF CV'leri hedef pozisyonlarla karşılaştıran ve veriye dayalı bir AI asistanı sunan uçtan uca bir kariyer zekâ platformudur.

Tüm sistem **sıfır zorunlu ücretli API maliyeti** prensibiyle tasarlanmıştır.

## 2. Mimari Katmanlar

```mermaid
flowchart LR
    subgraph Frontend["1. Sunum Katmanı (React 18 + TS + Tailwind + Recharts)"]
        Pages["8 Ana Modül Sayfası"]
        Hooks["Tema & API Servis Katmanı"]
    end

    subgraph Backend["2. Uygulama & İş Mantığı Katmanı (FastAPI)"]
        Routers["REST API (/api/v1/*)"]
        Importer["CSV Şema Eşleştirme & Deduplikasyon"]
        NLP["Türkçe/İngilizce Beceri Çıkarım Motoru"]
        Career["CV Analiz & Yol Haritası Motoru"]
        Assistant["Hibrit AI Asistanı (Ollama + Kural/İstatistik Fallback)"]
    end

    subgraph ML["3. Analitik ve Makine Öğrenmesi Katmanı"]
        Stats["Pazar, Şehir, Sektör & Birliktelik Analitiği"]
        Clf["İlan Sınıflandırma (TF-IDF + LogisticRegression)"]
        Forecast["Talep Tahmini (Holt Exponential Smoothing)"]
    end

    subgraph Data["4. Veri & Depolama Katmanı"]
        PG[("PostgreSQL 16 (16 Tablo)")]
        Artifacts[("Model Deposu (.joblib)")]
    end

    Frontend <--> Routers
    Routers --> Importer & NLP & Career & Assistant & Stats & Clf & Forecast
    Importer & NLP & Career & Stats <--> PG
    Clf & Forecast <--> PG
    Clf & Forecast <--> Artifacts
```

## 3. Servisler Arası İletişim ve Güvenlik

- **Docker Compose Ağı (`skillscope_network`):** `postgres`, `backend` ve `frontend` servisleri izole bridge ağında haberleşir.
- **Healthcheck Bağımlılığı:** PostgreSQL `pg_isready` kontrolünden geçmeden `backend` başlamaz; `backend` `/api/v1/health` kontrolünden geçmeden `frontend` trafiği açılmaz.
- **Gizlilik Odaklı CV İşleme:** Yüklenen PDF dosyaları diske yazılmadan `io.BytesIO` ile bellekte ayrıştırılır; CV metinleri loglanmaz ve harici servislere gönderilmez.
