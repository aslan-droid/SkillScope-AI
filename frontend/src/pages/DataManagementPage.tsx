import React, { useEffect, useState } from 'react';
import {
  CheckCircle2,
  Database,
  FileSpreadsheet,
  Globe,
  RefreshCw,
  Trash2,
  Upload,
} from 'lucide-react';
import { api } from '../services/api';
import type { DatasetItem } from '../types';
import { ErrorBanner, LoadingSpinner, SuccessBanner } from '../components/StatusUI';

export const DataManagementPage: React.FC = () => {
  const [datasets, setDatasets] = useState<DatasetItem[]>([]);
  const [syncStatus, setSyncStatus] = useState<{
    auto_sync_enabled: boolean;
    interval_minutes: number;
    real_jobs_count: number;
    demo_jobs_count: number;
    is_syncing: boolean;
    last_sync_at: string | null;
    next_sync_at: string | null;
    last_sync_status: string;
  } | null>(null);
  const [syncingLive, setSyncingLive] = useState(false);
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [sourceName, setSourceName] = useState('Kullanıcı CSV Veri Seti');
  const [licenseName, setLicenseName] = useState('CC-BY 4.0 / Açık Lisans');
  const [columnMappingJson, setColumnMappingJson] = useState('');

  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const fetchDatasets = async () => {
    setLoading(true);
    setError(null);
    try {
      const [res, syncRes] = await Promise.all([api.listDatasets(), api.getSyncStatus()]);
      setDatasets(res);
      setSyncStatus(syncRes);
    } catch (err: any) {
      setError(err.message || 'Veri setleri listelenemedi.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDatasets();
  }, []);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!csvFile) {
      setError('Lütfen içe aktarmak için bir CSV (.csv) dosyası seçin.');
      return;
    }
    setUploading(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const res = await api.uploadDatasetCsv(csvFile, sourceName, licenseName, columnMappingJson);
      setSuccessMsg(
        `'${res.filename}' doğrulandı: ${res.imported_rows} ilan kaydedildi, ${res.duplicate_rows} mükerrer ilan engellendi, ${res.extracted_skill_links} beceri eşleşmesi çıkarıldı.`
      );
      setCsvFile(null);
      await fetchDatasets();
    } catch (err: any) {
      setError(err.message || 'CSV yükleme başarısız oldu.');
    } finally {
      setUploading(false);
    }
  };

  const handleReloadDemo = async () => {
    setUploading(true);
    setError(null);
    setSuccessMsg(null);
    try {
      await api.loadDemoDataset(true);
      setSuccessMsg('Sentetik Demo Veri Seti (SYNTHETIC_DEMO) başarıyla yeniden yüklendi ve ML modelleri güncellendi.');
      await fetchDatasets();
    } catch (err: any) {
      setError(err.message || 'Demo veri seti yüklenemedi.');
    } finally {
      setUploading(false);
    }
  };

  const handleSyncLive = async () => {
    setSyncingLive(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const res = await api.syncLiveSources(['remotive', 'arbeitnow'], 80);
      setSuccessMsg(
        `Canlı API senkronizasyonu tamamlandı: ${res.total_imported} yeni gerçek ilan eklendi, ${res.total_duplicates} mükerrer atlandı, ${res.total_skill_links} beceri eşleşmesi çıkarıldı.`
      );
      await fetchDatasets();
    } catch (err: any) {
      setError(err.message || 'Canlı API senkronizasyonu başarısız oldu.');
    } finally {
      setSyncingLive(false);
    }
  };

  const handlePurgeDemo = async () => {
    setUploading(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const res = await api.purgeDemoData();
      setSuccessMsg(
        `Sentetik demo veriler temizlendi: ${res.deleted_jobs} demo ilan ve ${res.deleted_imports} demo kaydı silindi.`
      );
      await fetchDatasets();
    } catch (err: any) {
      setError(err.message || 'Demo veriler silinemedi.');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (datasetId: number, filename: string) => {
    setError(null);
    setSuccessMsg(null);
    try {
      await api.deleteDataset(datasetId);
      setSuccessMsg(`'${filename}' veri seti ve bağlı iş ilanları silindi.`);
      await fetchDatasets();
    } catch (err: any) {
      setError(err.message || 'Veri seti silinemedi.');
    }
  };

  return (
    <div className="space-y-6">
      {error && <ErrorBanner message={error} onRetry={() => setError(null)} />}
      {successMsg && <SuccessBanner message={successMsg} onClose={() => setSuccessMsg(null)} />}

      {/* Live Public API Sync Card */}
      <div className="rounded-2xl bg-white dark:bg-navy-900 p-6 border border-slate-200/80 dark:border-slate-800/80 shadow-xs">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="p-2.5 rounded-xl bg-emerald-500/15 text-emerald-600 dark:text-emerald-400">
              <Globe className="h-5 w-5" />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-base font-bold text-slate-900 dark:text-white">
                  Canlı Açık API Senkronizasyonu (Remotive & Arbeitnow)
                </h2>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/15 text-emerald-600 dark:text-emerald-400">
                  {syncStatus?.auto_sync_enabled
                    ? `Otomatik: Her ${Math.round((syncStatus.interval_minutes || 360) / 60)} saatte bir`
                    : 'Manuel Mod'}
                </span>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Ücretsiz ve yasal açık API uç noktalarından gerçek iş ilanlarını periyodik olarak çeker,
                mükerrerleri (SHA-256) eler ve NLP/ML modellerini günceller.
              </p>
              {syncStatus && (
                <div className="flex flex-wrap gap-4 mt-2 text-xs text-slate-600 dark:text-slate-300">
                  <span>
                    <strong>Gerçek İlan:</strong> {syncStatus.real_jobs_count}
                  </span>
                  <span>
                    <strong>Demo İlan:</strong> {syncStatus.demo_jobs_count}
                  </span>
                  <span>
                    <strong>Son Senkronizasyon:</strong>{' '}
                    {syncStatus.last_sync_at
                      ? new Date(syncStatus.last_sync_at).toLocaleString('tr-TR')
                      : 'Henüz yapılmadı'}
                  </span>
                </div>
              )}
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2.5">
            <button
              type="button"
              onClick={handleSyncLive}
              disabled={syncingLive}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-600 text-white text-xs font-semibold hover:bg-emerald-700 disabled:opacity-50 transition-colors"
            >
              <RefreshCw className={`h-4 w-4 ${syncingLive ? 'animate-spin' : ''}`} />
              {syncingLive ? 'Gerçek İlanlar Çekiliyor...' : 'Gerçek Verileri Şimdi Çek'}
            </button>
            {syncStatus && syncStatus.demo_jobs_count > 0 && (
              <button
                type="button"
                onClick={handlePurgeDemo}
                disabled={uploading}
                className="inline-flex items-center gap-2 px-3.5 py-2.5 rounded-xl bg-rose-500/10 text-rose-600 dark:text-rose-400 text-xs font-semibold hover:bg-rose-500/20 disabled:opacity-50 transition-colors"
              >
                <Trash2 className="h-4 w-4" />
                Demo Verileri Temizle ({syncStatus.demo_jobs_count})
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Top Grid: CSV Upload Form & Demo Dataset Control */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <form
          onSubmit={handleUpload}
          className="lg:col-span-8 rounded-2xl bg-white dark:bg-navy-900 p-6 border border-slate-200/80 dark:border-slate-800/80 shadow-xs space-y-4"
        >
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-brand-purple/15 text-brand-purple">
              <FileSpreadsheet className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900 dark:text-white">
                CSV İş İlanı Veri Seti İçe Aktarma Motoru
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Otomatik sütun eşleştirme, mükerrer ilan engelleme (SHA-256) ve NLP beceri çıkarımı
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Veri Kaynağı Adı
              </label>
              <input
                type="text"
                value={sourceName}
                onChange={(e) => setSourceName(e.target.value)}
                className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-navy-950 px-3 py-2 text-xs"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Lisans / Kullanım Koşulu
              </label>
              <input
                type="text"
                value={licenseName}
                onChange={(e) => setLicenseName(e.target.value)}
                className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-navy-950 px-3 py-2 text-xs"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Özel Sütun Eşleştirme JSON (İsteğe Bağlı — Türkçe/İngilizce başlıklar otomatik tanınır)
            </label>
            <input
              type="text"
              value={columnMappingJson}
              onChange={(e) => setColumnMappingJson(e.target.value)}
              placeholder='Örn: {"job_title": "PozisyonAdi", "description": "IlanDetayi", "location": "Il"}'
              className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-navy-950 px-3 py-2 text-xs font-mono"
            />
          </div>

          <label className="block border-2 border-dashed border-slate-300 dark:border-slate-700 hover:border-brand-teal rounded-2xl p-5 text-center cursor-pointer transition bg-slate-50/50 dark:bg-navy-950/50">
            <Upload className="h-6 w-6 mx-auto text-brand-teal mb-1.5" />
            <span className="text-xs font-semibold text-slate-800 dark:text-slate-200 block">
              {csvFile ? csvFile.name : 'CSV Dosyası Seçin (.csv, Maks. 15 MB)'}
            </span>
            <span className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5 block">
              Desteklenen sütunlar: job_title, company, location, description, employment_type, salary_min, salary_max,
              currency, remote_type, posted_date, source_url, source_name
            </span>
            <input
              type="file"
              accept=".csv,text/csv"
              onChange={(e) => setCsvFile(e.target.files?.[0] || null)}
              className="hidden"
            />
          </label>

          <button
            type="submit"
            disabled={uploading}
            className="w-full py-2.5 px-4 rounded-xl text-xs font-bold bg-gradient-to-r from-brand-purple to-brand-teal text-white hover:opacity-95 transition shadow-md disabled:opacity-50"
          >
            {uploading ? 'Veri Seti Doğrulanıyor ve İçe Aktarılıyor...' : 'CSV Veri Setini Doğrula ve İçe Aktar'}
          </button>
        </form>

        {/* Demo Dataset Card */}
        <div className="lg:col-span-4 rounded-2xl bg-white dark:bg-navy-900 p-6 border border-slate-200/80 dark:border-slate-800/80 shadow-xs flex flex-col justify-between space-y-4">
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-sm font-bold text-slate-900 dark:text-white">
              <Database className="h-4 w-4 text-brand-teal" />
              <span>Sentetik Demo Veri Seti Yönetimi</span>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
              Proje ilk açıldığında boş görünmemesi için <strong>SYNTHETIC_DEMO</strong> etiketli, Türkiye'deki
              şehirleri ve 8 aylık zaman serisini kapsayan 72 adet örnek ilan içerir.
            </p>
            <div className="p-3 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200/70 dark:border-slate-800 text-[11px] text-slate-500 dark:text-slate-400 space-y-1">
              <div>• Gerçek ilanlarla karıştırılmaz (`is_demo = True`).</div>
              <div>• Dashboard üzerinden tek tıkla filtrelenebilir.</div>
              <div>• İstediğiniz zaman aşağıdaki listeden silebilir veya sıfırlayabilirsiniz.</div>
            </div>
          </div>

          <button
            type="button"
            onClick={handleReloadDemo}
            disabled={uploading}
            className="w-full py-2.5 px-4 rounded-xl text-xs font-bold border border-brand-teal text-brand-teal hover:bg-brand-teal hover:text-white transition flex items-center justify-center gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${uploading ? 'animate-spin' : ''}`} />
            <span>Demo Veri Setini Sıfırla / Yeniden Yükle</span>
          </button>
        </div>
      </div>

      {/* Datasets Table */}
      <div className="rounded-2xl bg-white dark:bg-navy-900 p-6 border border-slate-200/80 dark:border-slate-800/80 shadow-xs space-y-4">
        <h3 className="text-base font-bold text-slate-900 dark:text-white">
          Yüklü Veri Setleri ve Doğrulama Geçmişi ({datasets.length})
        </h3>

        {loading ? (
          <LoadingSpinner label="Veri seti kayıtları yükleniyor..." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400">
                  <th className="py-3 px-3">Dosya Adı</th>
                  <th className="py-3 px-3">Veri Kaynağı & Lisans</th>
                  <th className="py-3 px-3">Tür</th>
                  <th className="py-3 px-3">İlan Sayısı (Net / Toplam)</th>
                  <th className="py-3 px-3">Mükerrer / Hatalı</th>
                  <th className="py-3 px-3">Doğrulama Durumu</th>
                  <th className="py-3 px-3">Yükleme Tarihi</th>
                  <th className="py-3 px-3 text-right">İşlem</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200/70 dark:divide-slate-800/70">
                {datasets.map((ds) => (
                  <tr key={ds.id} className="hover:bg-slate-50/80 dark:hover:bg-navy-950/50">
                    <td className="py-3.5 px-3 font-semibold text-slate-900 dark:text-white">{ds.filename}</td>
                    <td className="py-3.5 px-3">
                      <div className="font-medium text-slate-800 dark:text-slate-200">{ds.source_name}</div>
                      <div className="text-[11px] text-slate-500">{ds.license_name}</div>
                    </td>
                    <td className="py-3.5 px-3">
                      {ds.is_demo ? (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/15 text-amber-600 dark:text-amber-300">
                          SYNTHETIC_DEMO
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-brand-teal/15 text-brand-teal">
                          GERÇEK / CSV
                        </span>
                      )}
                    </td>
                    <td className="py-3.5 px-3 font-bold text-brand-purple dark:text-indigo-300">
                      {ds.imported_rows} / {ds.total_rows}
                    </td>
                    <td className="py-3.5 px-3 text-slate-500">
                      {ds.duplicate_rows} mükerrer • {ds.invalid_rows} geçersiz
                    </td>
                    <td className="py-3.5 px-3">
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/15 text-emerald-600 dark:text-emerald-300">
                        <CheckCircle2 className="h-3 w-3" />
                        {ds.validation_status}
                      </span>
                    </td>
                    <td className="py-3.5 px-3 text-slate-500">
                      {new Date(ds.created_at).toLocaleString('tr-TR')}
                    </td>
                    <td className="py-3.5 px-3 text-right">
                      <button
                        onClick={() => handleDelete(ds.id, ds.filename)}
                        className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-semibold text-rose-500 hover:bg-rose-500/10 transition"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                        <span>Sil</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
