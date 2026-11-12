# SkillScope AI — Veritabanı Şeması (`docs/database-schema.md`)

Veritabanı **PostgreSQL 16** üzerinde çalışacak şekilde **SQLAlchemy 2.0 ORM** ve **Alembic** migration sistemiyle modellenmiştir. Toplam **16 ilişkisel tablo** bulunmaktadır:

## Tablo Listesi ve Rolleri

| # | Tablo Adı | Birincil Anahtar | Yabancı Anahtarlar & İndeksler | Açıklama |
| :--- | :--- | :--- | :--- | :--- |
| 1 | `users` | `id` | `email (UNIQUE, INDEX)` | Kullanıcı profilleri, hedef rol ve PBKDF2-SHA256 parola özeti |
| 2 | `companies` | `id` | `name (UNIQUE, INDEX)`, `sector (INDEX)` | İlan veren kurumlar ve sektörleri |
| 3 | `categories` | `id` | `name (UNIQUE)`, `slug (UNIQUE)` | 7 standart iş ilanı sınıflandırma kategorisi |
| 4 | `data_sources` | `id` | `name (UNIQUE)`, `is_synthetic (INDEX)` | Veri kaynakları (`SYNTHETIC_DEMO`, `CSV_UPLOAD`, `OPEN_DATASET`) ve lisans bilgileri |
| 5 | `dataset_imports` | `id` | `data_source_id (FK)`, `is_demo (INDEX)` | CSV yükleme geçmişi, satır doğrulama ve mükerrer kayıt istatistikleri |
| 6 | `jobs` | `id` | `company_id (FK)`, `category_id (FK)`, `dataset_import_id (FK)`, `content_hash (UNIQUE)` | İş ilanları, normalize pozisyon, şehir, çalışma modeli, maaş ve tarih |
| 7 | `skills` | `id` | `name (UNIQUE)`, `slug (UNIQUE)`, `category (INDEX)` | Yönetilebilir beceri sözlüğü, eş anlamlılar (`aliases`), önkoşullar ve ücretsiz kaynaklar |
| 8 | `job_skills` | `id` | `job_id (FK)`, `skill_id (FK)`, `uq_job_skill (UNIQUE)` | İlan-Beceri çoka-çok ilişki tablosu ve eşleşen terim güven skoru |
| 9 | `analysis_results` | `id` | `analysis_type (INDEX)`, `scope_key (INDEX)` | Önbelleklenen veya kaydedilen piyasa analiz çıktıları |
| 10 | `model_versions` | `id` | `model_name (INDEX)`, `model_type (INDEX)` | Eğitilen ML modellerinin versiyonları, MAE/RMSE/F1 metrikleri ve karşılaştırma verisi |
| 11 | `user_skills` | `id` | `user_id (FK)`, `skill_id (FK)`, `uq_user_skill (UNIQUE)` | Kullanıcının sahip olduğu beceriler ve yetkinlik seviyeleri |
| 12 | `cv_analyses` | `id` | `user_id (FK)`, `target_role (INDEX)` | CV analiz özetleri, eşleşen/eksik beceriler ve öğrenme öncelikleri |
| 13 | `career_roadmaps` | `id` | `user_id (FK)`, `target_role (INDEX)` | Kişiselleştirilmiş kariyer gelişim yol haritası üst kaydı |
| 14 | `roadmap_items` | `id` | `roadmap_id (FK)` | Yol haritasının sıralı adımları, tahmini saat/hafta ve proje hedefleri |
| 15 | `chat_sessions` | `id` | `user_id (FK)` | AI Kariyer Asistanı sohbet oturumları |
| 16 | `chat_messages` | `id` | `session_id (FK)` | Sohbet mesajları, kullanılan motor (`OLLAMA` veya `FALLBACK`) ve kanıt meta verileri |
