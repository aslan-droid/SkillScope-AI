# SkillScope AI — REST API Dokümantasyonu (`docs/api-documentation.md`)

Backend servisi çalıştığında etkileşimli **Swagger UI** dokümantasyonuna `http://localhost:8000/docs` adresinden, **ReDoc** arayüzüne ise `http://localhost:8000/redoc` adresinden erişilebilir.

## Temel Endpoint Grupları (`/api/v1`)

### 1. Sistem & Sağlık
- `GET /api/v1/health` — Veritabanı bağlantısını, toplam ilan ve beceri sayısını döner.

### 2. İş İlanları (`/api/v1/jobs`)
- `GET /api/v1/jobs` — Sayfalı (`page`, `page_size`) ve filtreli (`city`, `role`, `sector`, `skill`, `remote_type`, `search`, `include_demo`) iş ilanı listesi.
- `GET /api/v1/jobs/{job_id}` — Tekil ilan detayı ve çıkarılan beceriler.
- `POST /api/v1/jobs` — Yeni iş ilanı ekler, SHA-256 ile mükerrer kontrolü yapar ve NLP ile becerileri çıkarır.
- `DELETE /api/v1/jobs/{job_id}` — İlanı siler.

### 3. Beceri Sözlüğü ve Keşif (`/api/v1/skills`)
- `GET /api/v1/skills` — Sözlükteki tüm becerileri ve ilanlardaki talep yüzdelerini listeler.
- `POST /api/v1/skills` — Sözlüğe yeni beceri, kategori, eş anlamlı (`aliases`) ve önkoşul ekler.
- `POST /api/v1/skills/extract` — Verilen metinden becerileri çıkarır ve kategorilere gruplar.
- `GET /api/v1/skills/{skill_identifier}` — Seçilen beceri (örn. `sql`) için birliktelik (`co_occurring_skills`), pozisyon, sektör, şehir dağılımı ve zaman serisi tahminini döner.

### 4. İş Piyasası Analitiği (`/api/v1/analytics`)
- `GET /api/v1/analytics/dashboard` — Dashboard KPI kartları, en çok aranan 10 beceri, pozisyon/şehir/sektör dağılımları ve aylık trendler.
- `GET /api/v1/analytics/market` — Çoklu filtreleme destekli piyasa ve maaş dağılım analitiği.

### 5. CV Analiz Modülü (`/api/v1/cv`)
- `POST /api/v1/cv/analyze` — `multipart/form-data` ile yüklenen PDF CV'yi bellekte analiz eder, becerileri sınıflandırır ve hedef pozisyonla karşılaştırır.
- `GET /api/v1/cv/history` — Kaydedilen CV analiz özetlerini listeler.
- `DELETE /api/v1/cv/{analysis_id}` — Kullanıcının CV analiz kaydını kalıcı olarak siler.

### 6. Kariyer Eşleştirme ve Yol Haritası (`/api/v1/career`)
- `GET /api/v1/career/roles` — Hedeflenebilecek meslekleri ve en çok aranan becerilerini listeler.
- `POST /api/v1/career/match` — Manuel seçilen becerilerle hedef pozisyon boşluk analizi yapar.
- `POST /api/v1/career/roadmap` — Önkoşul ve talep sıklığına dayalı haftalık öğrenme yol haritası üretir.

### 7. Katmanlı AI Asistanı (`/api/v1/assistant`)
- `GET /api/v1/assistant/status` — Yerel Ollama durumunu, yapılandırılan modeli ve örnek soruları döner.
- `POST /api/v1/assistant/ask` — Soruyu veritabanı analiz fonksiyonlarıyla (Ollama açıksa LLM ile, kapalıysa Kural/İstatistik Fallback ile) yanıtlar ve `evidence` (veri dönemi, örneklem büyüklüğü, kaynak, sınırlılıklar) döner.

### 8. Veri Yönetimi (`/api/v1/datasets`)
- `GET /api/v1/datasets` — Yüklenen veri setlerini ve doğrulama özetlerini listeler.
- `POST /api/v1/datasets/upload` — CSV dosyası yükler, sütunları eşleştirir ve doğrular.
- `POST /api/v1/datasets/load-demo` — Açık etiketli sentetik demo veri setini (`SYNTHETIC_DEMO`) yükler/sıfırlar.
- `DELETE /api/v1/datasets/{dataset_id}` — Veri setini ve bağlı ilanları siler.

### 9. Makine Öğrenmesi Modelleri (`/api/v1/models`)
- `GET /api/v1/models` — Eğitilen modelleri, versiyonlarını ve metriklerini (`MAE`, `RMSE`, `Accuracy`, `Precision`, `Recall`, `F1`) listeler.
- `POST /api/v1/models/train` — Sınıflandırma ve tahmin modellerini güncel verilerle yeniden eğitir.
- `GET /api/v1/models/forecast/{skill_identifier}` — Beceri için zaman serisi talep tahmini döner.
- `POST /api/v1/models/classify` — İlan başlığı ve açıklamasını 7 kategoriden birine sınıflandırır.
