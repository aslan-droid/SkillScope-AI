# SkillScope AI — Veri Dizini (`data/`)

Bu klasör SkillScope AI platformuna ait veri şablonlarını, sentetik demo veri setini ve yerel ortamda yüklenen/işlenen dosyaları barındırır.

## Klasör Yapısı

- `sample/`: Proje ilk ayağa kalktığında kullanılan ve **açıkça sentetik (`SYNTHETIC_DEMO`) olarak etiketlenen** demo veri seti (`demo_jobs_tr.csv`) ile örnek CSV yükleme şablonunu içerir.
- `raw/`: Kullanıcının yerel olarak test amaçlı koyabileceği ham CSV dosyaları (Git'e dahil edilmez).
- `processed/`: Veri temizleme ve normalizasyon boru hattından (pipeline) geçmiş çıktılar (Git'e dahil edilmez).

## Desteklenen CSV Sütun Şeması

Standart sütunlar:
- `job_title` (Zorunlu): İlan başlığı (Örn: "Veri Analisti", "Kıdemli Backend Geliştirici")
- `company`: Şirket adı
- `location`: Şehir / Konum (Örn: "İstanbul", "Ankara", "Gaziantep", "İzmir")
- `description` (Zorunlu): İlan açıklaması ve aranan nitelikler metni
- `employment_type`: Çalışma tipi (`Tam Zamanlı`, `Yarı Zamanlı`, `Stajyer`, `Sözleşmeli`)
- `salary_min`: Minimum maaş (sayısal, isteğe bağlı)
- `salary_max`: Maksimum maaş (sayısal, isteğe bağlı)
- `currency`: Para birimi (`TRY`, `USD`, `EUR`)
- `remote_type`: Çalışma modeli (`Uzaktan`, `Hibrit`, `Ofisten`)
- `posted_date`: İlan yayın tarihi (`YYYY-MM-DD`)
- `source_url`: İlanın orijinal bağlantısı
- `source_name`: Veri kaynağı adı
- `sector`: Sektör bilgisi (İsteğe bağlı; yoksa sınıflandırıcı tarafından tahmin edilir)

> **Not:** Farklı sütun adlarına sahip CSV dosyaları (`ilan_basligi`, `sehir`, `aciklama`, `sirket` vb.) backend içe aktarma motoru tarafından otomatik olarak standart şemaya eşleştirilir.
