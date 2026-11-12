import React from 'react';
import { CheckCircle2, Code2, Database, Lock, Scale, Server, Sparkles } from 'lucide-react';

export const AboutPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="rounded-2xl bg-gradient-to-br from-navy-900 to-navy-800 p-8 text-white border border-slate-700/80 shadow-lg space-y-4">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-teal/20 border border-brand-teal/40 text-brand-teal text-xs font-bold">
          <Sparkles className="h-3.5 w-3.5" />
          <span>SkillScope AI v1.0 — Açık Kaynak Kariyer & İş Piyasası Zekâ Platformu</span>
        </div>
        <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
          Dağınık İş İlanı Verilerini Kişiselleştirilmiş Kariyer Kararlarına Dönüştürün
        </h2>
        <p className="text-sm text-slate-300 max-w-3xl leading-relaxed">
          SkillScope AI; iş arayan öğrencilerin, yeni mezunların ve kariyerini geliştirmek isteyen profesyonellerin
          hangi teknolojilerin talep gördüğünü, becerilerin hangi pozisyon ve şehirlerde yoğunlaştığını ve hedefledikleri
          meslek için hangi yetkinlik açıklarını kapatmaları gerektiğini <strong>sıfır ücretli API maliyetiyle</strong>{' '}
          analiz eden uçtan uca bir yazılım ürünüdür.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="rounded-2xl bg-white dark:bg-navy-900 p-6 border border-slate-200/80 dark:border-slate-800/80 shadow-xs space-y-3">
          <div className="flex items-center gap-2.5 text-sm font-bold text-slate-900 dark:text-white">
            <Server className="h-5 w-5 text-brand-purple" />
            <span>Teknoloji Yığını (Sıfır Bütçe)</span>
          </div>
          <ul className="text-xs text-slate-600 dark:text-slate-300 space-y-2">
            <li className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
              <span><strong>Backend:</strong> Python 3.11, FastAPI, SQLAlchemy 2.0, Pydantic v2, Alembic</span>
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
              <span><strong>Veritabanı:</strong> PostgreSQL 16 (16 ilişkisel tablo, indeks ve kısıtlar)</span>
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
              <span><strong>Veri Bilimi & ML:</strong> Pandas, NumPy, Scikit-learn, Statsmodels, PyPDF</span>
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
              <span><strong>Frontend:</strong> React 18, TypeScript, Vite, Tailwind CSS, Recharts</span>
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
              <span><strong>Yerel AI & Fallback:</strong> Opsiyonel Ollama + Kural/Retrieval Analitik Motoru</span>
            </li>
          </ul>
        </div>

        <div className="rounded-2xl bg-white dark:bg-navy-900 p-6 border border-slate-200/80 dark:border-slate-800/80 shadow-xs space-y-3">
          <div className="flex items-center gap-2.5 text-sm font-bold text-slate-900 dark:text-white">
            <Database className="h-5 w-5 text-brand-teal" />
            <span>Veri Kaynakları ve Etik Kurallar</span>
          </div>
          <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
            LinkedIn, Kariyer.net veya Indeed gibi platformlardan izinsiz veri kazıma (scraping) veya CAPTCHA aşma
            girişimi <strong>kesinlikle yapılmaz</strong>.
          </p>
          <ul className="text-xs text-slate-600 dark:text-slate-300 space-y-1.5 list-disc list-inside">
            <li>Kullanıcı tarafından yüklenen CSV veri setleri</li>
            <li>Açıkça <code>SYNTHETIC_DEMO</code> olarak etiketlenen başlangıç veri seti</li>
            <li>ESCO ve O*NET açık meslek/beceri taksonomileri (CC-BY 4.0)</li>
            <li>Kamuya açık istatistik bültenleri</li>
          </ul>
        </div>

        <div className="rounded-2xl bg-white dark:bg-navy-900 p-6 border border-slate-200/80 dark:border-slate-800/80 shadow-xs space-y-3">
          <div className="flex items-center gap-2.5 text-sm font-bold text-slate-900 dark:text-white">
            <Lock className="h-5 w-5 text-emerald-500" />
            <span>Güvenlik, Gizlilik ve Sınırlılıklar</span>
          </div>
          <ul className="text-xs text-slate-600 dark:text-slate-300 space-y-2">
            <li>
              <strong>CV Gizliliği:</strong> PDF CV dosyaları diske kalıcı yazılmaz, bellekte işlenir, loglanmaz ve
              kullanıcı istediği an analiz kaydını silebilir.
            </li>
            <li>
              <strong>Eşleşme Skoru Sınırlılığı:</strong> Gösterilen beceri uyum yüzdesi işe alınma olasılığı değil,
              ilanlardaki teknik beceri gereksinimleriyle örtüşme oranıdır.
            </li>
            <li>
              <strong>Tahmin Sınırlılığı:</strong> Zaman serisi tahminleri yüklü veri kapsamına bağlıdır; veri
              yetersizliğinde otomatik olarak kapatılır.
            </li>
          </ul>
        </div>
      </div>

      <div className="rounded-2xl bg-white dark:bg-navy-900 p-6 border border-slate-200/80 dark:border-slate-800/80 shadow-xs flex flex-wrap items-center justify-between gap-4 text-xs">
        <div className="flex items-center gap-2 text-slate-600 dark:text-slate-300">
          <Scale className="h-4 w-4 text-brand-purple" />
          <span>
            <strong>Açık Kaynak Lisansı:</strong> MIT License • Tüm bağımlılıklar MIT, Apache-2.0 ve BSD-3-Clause
            uyumludur.
          </span>
        </div>
        <div className="flex items-center gap-2 text-brand-teal font-semibold">
          <Code2 className="h-4 w-4" />
          <span>Swagger API Dokümantasyonu: http://localhost:8000/docs</span>
        </div>
      </div>
    </div>
  );
};
