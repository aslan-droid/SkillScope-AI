import React, { useEffect, useState } from 'react';
import {
  Area,
  ComposedChart,
  CartesianGrid,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { Activity, AlertTriangle, CheckCircle2, Cpu, Play, Sparkles, TrendingUp } from 'lucide-react';
import { api } from '../services/api';
import type { ModelVersionItem, SkillForecastResponse } from '../types';
import { ErrorBanner, LoadingSpinner, SuccessBanner } from '../components/StatusUI';

const FORECAST_SKILLS = ['SQL', 'Python', 'Power BI', 'Docker', 'TypeScript', 'PostgreSQL', 'Machine Learning'];

export const ModelPerformancePage: React.FC = () => {
  const [models, setModels] = useState<ModelVersionItem[]>([]);
  const [selectedSkill, setSelectedSkill] = useState('SQL');
  const [forecast, setForecast] = useState<SkillForecastResponse | null>(null);

  const [testTitle, setTestTitle] = useState('Kıdemli Veri Analisti (SQL & Power BI)');
  const [testDesc, setTestDesc] = useState(
    'Finansal veri ambarında SQL, Power BI, Excel ve Python Pandas ile KPI raporlaması ve istatistiksel analiz yapacak uzman.'
  );
  const [clfOutput, setClfOutput] = useState<{
    predicted_category: string;
    confidence: number;
    probabilities: Record<string, number>;
    is_experimental: boolean;
  } | null>(null);

  const [loading, setLoading] = useState(true);
  const [training, setTraining] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const loadModelsAndForecast = async (skillName = selectedSkill) => {
    setLoading(true);
    setError(null);
    try {
      const [mList, fcRes] = await Promise.all([
        api.listModels(),
        api.getSkillForecast(skillName, 3, true),
      ]);
      setModels(mList);
      setForecast(fcRes);
    } catch (err: any) {
      setError(err.message || 'Model performans verileri alınamadı.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadModelsAndForecast(selectedSkill);
  }, [selectedSkill]);

  const handleRetrainAll = async () => {
    setTraining(true);
    setError(null);
    setSuccessMsg(null);
    try {
      await api.trainModels();
      setSuccessMsg('Sınıflandırma (TF-IDF + LogisticRegression) ve Zaman Serisi Tahmin modelleri yeniden eğitildi.');
      await loadModelsAndForecast(selectedSkill);
    } catch (err: any) {
      setError(err.message || 'Model eğitimi başarısız oldu.');
    } finally {
      setTraining(false);
    }
  };

  const handleTestClassifier = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await api.classifyJobText({ job_title: testTitle, description: testDesc });
      setClfOutput(res);
    } catch (err: any) {
      setError(err.message || 'Sınıflandırma hatası.');
    }
  };

  const latestClassifier = models.find((m) => m.model_type === 'JOB_CLASSIFIER');

  // Birleştirilmiş zaman serisi grafik verisi: Geçmiş + Test Tahmini + Gelecek Tahmin & Aralık
  const combinedChartData = React.useMemo(() => {
    if (!forecast || !forecast.forecast_available) return [];
    const points: Array<Record<string, any>> = [];
    forecast.history.forEach((h) => {
      points.push({
        period: h.period,
        actual: h.actual,
        test_predicted: h.test_predicted ?? null,
        forecast_predicted: null,
        lower_bound: null,
        upper_bound: null,
      });
    });
    forecast.forecast.forEach((f) => {
      points.push({
        period: f.period,
        actual: null,
        test_predicted: null,
        forecast_predicted: f.predicted,
        lower_bound: f.lower_bound,
        upper_bound: f.upper_bound,
      });
    });
    return points;
  }, [forecast]);

  if (loading && models.length === 0) {
    return <LoadingSpinner label="Makine öğrenmesi modelleri ve değerlendirme metrikleri yükleniyor..." />;
  }

  return (
    <div className="space-y-6">
      {error && <ErrorBanner message={error} onRetry={() => loadModelsAndForecast(selectedSkill)} />}
      {successMsg && <SuccessBanner message={successMsg} onClose={() => setSuccessMsg(null)} />}

      {/* Header & Retrain Trigger */}
      <div className="rounded-2xl bg-white dark:bg-navy-900 p-5 border border-slate-200/80 dark:border-slate-800/80 shadow-xs flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-brand-purple/15 text-brand-purple">
            <Cpu className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-900 dark:text-white">
              Makine Öğrenmesi Model Yönetimi ve Değerlendirme Merkezi
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Notebook bağımsız üretim boru hattı (`backend/app/ml` & `ml/models/*.joblib`)
            </p>
          </div>
        </div>

        <button
          onClick={handleRetrainAll}
          disabled={training}
          className="px-4 py-2.5 rounded-xl text-xs font-bold bg-gradient-to-r from-brand-purple to-brand-teal text-white hover:opacity-95 transition shadow-md disabled:opacity-50 flex items-center gap-2"
        >
          <Play className="h-3.5 w-3.5" />
          <span>{training ? 'Modeller Eğitiliyor...' : 'Modelleri Güncel Veriyle Yeniden Eğit'}</span>
        </button>
      </div>

      {/* Section A: Skill Demand Time-Series Forecasting */}
      <div className="rounded-2xl bg-white dark:bg-navy-900 p-6 border border-slate-200/80 dark:border-slate-800/80 shadow-xs space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-brand-teal" />
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                A. Beceri Talep Tahmini (Zaman Serisi Analizi — MAE & RMSE)
              </h3>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Zamana dayalı eğitim/test ayrımı (Temporal Split), geçmiş değerler, tahmin edilen değerler ve güven aralığı
            </p>
          </div>

          <div className="flex flex-wrap gap-1.5">
            {FORECAST_SKILLS.map((sk) => (
              <button
                key={sk}
                onClick={() => setSelectedSkill(sk)}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition ${
                  selectedSkill === sk
                    ? 'bg-brand-teal text-white shadow-xs'
                    : 'bg-slate-100 dark:bg-navy-800 text-slate-700 dark:text-slate-300'
                }`}
              >
                {sk}
              </button>
            ))}
          </div>
        </div>

        {forecast && !forecast.forecast_available ? (
          <div className="p-5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-xs text-amber-800 dark:text-amber-200 flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 shrink-0 text-amber-500" />
            <div>
              <p className="font-bold">Tahmin Özelliği Bu Beceri İçin Devre Dışı Bırakıldı</p>
              <p className="mt-1">{forecast.reason}</p>
            </div>
          </div>
        ) : forecast && forecast.forecast_available ? (
          <>
            {/* Metrics Strip */}
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
              <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200/70 dark:border-slate-800">
                <span className="text-[11px] text-slate-500 block">MAE (Ortalama Mutlak Hata)</span>
                <span className="text-lg font-extrabold text-brand-teal">{forecast.metrics?.mae}</span>
              </div>
              <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200/70 dark:border-slate-800">
                <span className="text-[11px] text-slate-500 block">RMSE (Kök Ort. Kare Hata)</span>
                <span className="text-lg font-extrabold text-brand-purple dark:text-indigo-300">
                  {forecast.metrics?.rmse}
                </span>
              </div>
              <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200/70 dark:border-slate-800">
                <span className="text-[11px] text-slate-500 block">Eğitim / Test Dönemi</span>
                <span className="text-sm font-bold text-slate-800 dark:text-slate-200">
                  {forecast.metrics?.train_months} Ay / {forecast.metrics?.test_months} Ay
                </span>
              </div>
              <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200/70 dark:border-slate-800">
                <span className="text-[11px] text-slate-500 block">Veri Dönemi</span>
                <span className="text-xs font-bold text-slate-800 dark:text-slate-200">{forecast.data_period}</span>
              </div>
              <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200/70 dark:border-slate-800">
                <span className="text-[11px] text-slate-500 block">Toplam Gözlem</span>
                <span className="text-lg font-extrabold text-emerald-500">
                  {forecast.metrics?.total_observations} İlan
                </span>
              </div>
            </div>

            {forecast.disclaimer && (
              <div className="text-[11px] px-3.5 py-2 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-800 dark:text-cyan-200">
                <strong>Not:</strong> {forecast.disclaimer}
              </div>
            )}

            {/* Chart & Actual vs Predicted Table */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              <div className="lg:col-span-8 h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={combinedChartData} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.2} />
                    <XAxis dataKey="period" tick={{ fontSize: 11, fill: '#94a3b8' }} />
                    <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#0B132B',
                        borderColor: '#334155',
                        borderRadius: '12px',
                        color: '#f8fafc',
                        fontSize: '12px',
                      }}
                    />
                    <Legend wrapperStyle={{ fontSize: '11px' }} />
                    <Area
                      type="monotone"
                      dataKey="upper_bound"
                      name="Tahmin Üst Sınırı (%90)"
                      stroke="none"
                      fill="#06B6D4"
                      fillOpacity={0.18}
                    />
                    <Area
                      type="monotone"
                      dataKey="lower_bound"
                      name="Tahmin Alt Sınırı (%90)"
                      stroke="none"
                      fill="#6366F1"
                      fillOpacity={0.12}
                    />
                    <Line
                      type="monotone"
                      dataKey="actual"
                      name="Gerçekleşen İlan Sayısı"
                      stroke="#6366F1"
                      strokeWidth={3}
                      dot={{ r: 4 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="test_predicted"
                      name="Test Dönemi Model Tahmini"
                      stroke="#F59E0B"
                      strokeWidth={2.5}
                      strokeDasharray="5 5"
                      dot={{ r: 4 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="forecast_predicted"
                      name="Gelecek Dönem Tahmini"
                      stroke="#10B981"
                      strokeWidth={3}
                      strokeDasharray="4 4"
                      dot={{ r: 5 }}
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>

              <div className="lg:col-span-4 space-y-3">
                <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200">
                  Test Verisi: Gerçek vs Tahmin Karşılaştırması
                </h4>
                <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-100 dark:bg-navy-950 text-slate-500">
                      <tr>
                        <th className="py-2 px-3">Dönem</th>
                        <th className="py-2 px-3">Gerçek</th>
                        <th className="py-2 px-3">Tahmin</th>
                        <th className="py-2 px-3">Mutlak Hata</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                      {forecast.comparison?.map((c) => (
                        <tr key={c.period}>
                          <td className="py-2 px-3 font-medium">{c.period}</td>
                          <td className="py-2 px-3 font-bold text-brand-purple dark:text-indigo-300">{c.actual}</td>
                          <td className="py-2 px-3 font-bold text-amber-500">{c.predicted}</td>
                          <td className="py-2 px-3 text-slate-500">{c.error}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <h4 className="text-xs font-bold text-emerald-600 dark:text-emerald-400 pt-2">
                  Gelecek 3 Dönem Tahmini ve Güven Aralığı
                </h4>
                <div className="space-y-1.5">
                  {forecast.forecast.map((f) => (
                    <div
                      key={f.period}
                      className="flex items-center justify-between px-3 py-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-xs"
                    >
                      <span className="font-bold">{f.period}</span>
                      <span className="font-extrabold text-emerald-600 dark:text-emerald-300">
                        {f.predicted} İlan
                      </span>
                      <span className="text-[11px] text-slate-500">
                        [{f.lower_bound} — {f.upper_bound}]
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </>
        ) : null}
      </div>

      {/* Section B: Job Classification Model & Live Interactive Tester */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-7 rounded-2xl bg-white dark:bg-navy-900 p-6 border border-slate-200/80 dark:border-slate-800/80 shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-brand-purple" />
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                B. İş İlanı Sınıflandırma Modeli (TF-IDF + LogisticRegression)
              </h3>
            </div>
            {latestClassifier && (
              <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-brand-purple/15 text-brand-purple dark:text-indigo-300">
                v{latestClassifier.version}
              </span>
            )}
          </div>

          {latestClassifier && (
            <>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200/70 dark:border-slate-800">
                  <span className="text-[10px] text-slate-500 block">Accuracy (Doğruluk)</span>
                  <span className="text-lg font-extrabold text-emerald-500">
                    %{(Number(latestClassifier.metrics.accuracy || 0) * 100).toFixed(1)}
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200/70 dark:border-slate-800">
                  <span className="text-[10px] text-slate-500 block">Precision (Kesinlik)</span>
                  <span className="text-lg font-extrabold text-brand-teal">
                    %{(Number(latestClassifier.metrics.precision || 0) * 100).toFixed(1)}
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200/70 dark:border-slate-800">
                  <span className="text-[10px] text-slate-500 block">Recall (Duyarlılık)</span>
                  <span className="text-lg font-extrabold text-brand-purple dark:text-indigo-300">
                    %{(Number(latestClassifier.metrics.recall || 0) * 100).toFixed(1)}
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200/70 dark:border-slate-800">
                  <span className="text-[10px] text-slate-500 block">F1-Score (Ağırlıklı)</span>
                  <span className="text-lg font-extrabold text-amber-500">
                    %{(Number(latestClassifier.metrics.f1_score || 0) * 100).toFixed(1)}
                  </span>
                </div>
              </div>

              <div className="space-y-2">
                <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300">
                  Test Kümesi: Gerçek ve Tahmin Edilen Kategori Karşılaştırmaları
                </h4>
                <div className="max-h-56 overflow-y-auto rounded-xl border border-slate-200 dark:border-slate-800">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-100 dark:bg-navy-950 text-slate-500 sticky top-0">
                      <tr>
                        <th className="py-2 px-3">Örnek İlan Metni</th>
                        <th className="py-2 px-3">Gerçek</th>
                        <th className="py-2 px-3">Tahmin</th>
                        <th className="py-2 px-3">Durum</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                      {latestClassifier.comparison_data.map((row, idx) => (
                        <tr key={idx}>
                          <td className="py-2 px-3 text-[11px] text-slate-600 dark:text-slate-300 max-w-xs truncate">
                            {row.sample}
                          </td>
                          <td className="py-2 px-3 font-medium">{row.actual}</td>
                          <td className="py-2 px-3 font-semibold text-brand-teal">{row.predicted}</td>
                          <td className="py-2 px-3">
                            {row.correct ? (
                              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                            ) : (
                              <AlertTriangle className="h-4 w-4 text-amber-500" />
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Live Classifier Sandbox */}
        <form
          onSubmit={handleTestClassifier}
          className="lg:col-span-5 rounded-2xl bg-white dark:bg-navy-900 p-6 border border-slate-200/80 dark:border-slate-800/80 shadow-xs space-y-4"
        >
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-brand-teal" />
            <h3 className="text-base font-bold text-slate-900 dark:text-white">
              Canlı İlan Sınıflandırma Test Aracı
            </h3>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Desteklenen 7 kategori: Yazılım geliştirme, Veri analizi, Yapay zekâ, Siber güvenlik, İş analizi, Sistem
            ve ağ, Diğer
          </p>

          <div>
            <label className="block text-xs font-semibold mb-1">İlan Başlığı</label>
            <input
              type="text"
              value={testTitle}
              onChange={(e) => setTestTitle(e.target.value)}
              className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-navy-950 px-3 py-2 text-xs"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold mb-1">İlan Açıklaması</label>
            <textarea
              rows={3}
              value={testDesc}
              onChange={(e) => setTestDesc(e.target.value)}
              className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-navy-950 px-3 py-2 text-xs"
            />
          </div>

          <button
            type="submit"
            className="w-full py-2.5 px-4 rounded-xl text-xs font-bold bg-brand-purple text-white hover:bg-indigo-500 transition"
          >
            ML Modeliyle Kategoriyi Tahmin Et
          </button>

          {clfOutput && (
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-slate-800 space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Tahmin Edilen Kategori:</span>
                <span className="font-extrabold text-brand-teal text-sm">{clfOutput.predicted_category}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Model Güven Skoru:</span>
                <span className="font-bold">%{(clfOutput.confidence * 100).toFixed(1)}</span>
              </div>
              {clfOutput.is_experimental && (
                <div className="text-[11px] text-amber-500">
                  * Deneysel Etiket: Eğitim verisi 50 gerçek ilanın altında olduğunda deneysel mod işaretlenir.
                </div>
              )}
            </div>
          )}
        </form>
      </div>
    </div>
  );
};
