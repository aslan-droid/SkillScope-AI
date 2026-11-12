# SkillScope AI — Veri Kaynakları ve Etik Kullanım Politikası (`docs/data-sources.md`)

## 1. Veri Toplama İlkeleri

SkillScope AI, telif haklarına, kişisel verilerin korunmasına ve web sitelerinin kullanım koşullarına (Terms of Service) tam uyum sağlar:
- LinkedIn, Kariyer.net, Indeed, Glassdoor gibi sitelerden **izinsiz veri kazıma (scraping) yapılmaz**.
- CAPTCHA, anti-bot veya erişim engellerini aşmaya yönelik hiçbir mekanizma içermez.
- Ücretli veri sağlayıcılarına bağımlı değildir.

## 2. Desteklenen Veri Kaynakları

1. **Kullanıcı Tarafından Yüklenen CSV Veri Setleri (`CSV_UPLOAD`):**
   - Üniversite kariyer merkezleri, araştırma grupları veya bireysel kullanıcıların sahip olduğu CSV dosyaları otomatik sütun eşleştirme ile sisteme aktarılır.
2. **Açık Etiketli Sentetik Demo Veri Seti (`SYNTHETIC_DEMO`):**
   - Dosya: `data/sample/demo_jobs_tr.csv`
   - Lisans: MIT
   - Açıklama: Sistem ilk kurulduğunda grafiklerin ve zaman serisi analizlerinin test edilebilmesi için oluşturulmuş 72 adet sentetik iş ilanıdır. Veritabanında `is_demo = True` olarak işaretlenir ve arayüzde açıkça belirtilir.
3. **Uyumlu Kamuya Açık Veri Kaynakları (`OPEN_DATASET`):**
   - **ESCO (European Skills, Competences, Qualifications and Occupations):** CC-BY 4.0 lisanslı Avrupa Komisyonu meslek ve beceri taksonomisi.
   - **O*NET Database:** CC-BY 4.0 lisanslı mesleki yetkinlik veri tabanı.
   - **İŞKUR & TÜİK Açık İstatistik Tabloları:** Kamuya açık yayınlanan istihdam verileri CSV şablonuna dönüştürülerek içe aktarılabilir.
