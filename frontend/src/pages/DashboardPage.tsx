import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import {
  ArrowUpRight,
  Briefcase,
  Building2,
  Calendar,
  Globe2,
  MapPin,
  Sparkles,
  TrendingUp,
} from 'lucide-react';
import { api } from '../services/api';
import type { DashboardSummary } from '../types';
import { EmptyState, ErrorBanner, LoadingSpinner, SyntheticDataBanner } from '../components/StatusUI';

const CHART_COLORS = ['#6366F1', '#06B6D4', '#8B5CF6', '#10B981', '#F59E0B', '#EC4899', '#3B82F6', '#14B8A6'];

export const DashboardPage: React.FC = () => {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [includeDemo, setIncludeDemo] = useState(true);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const fetchDashboard = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getDashboardSummary(includeDemo);
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Dashboard verileri yüklenemedi.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, [includeDemo]);

  if (loading) return <LoadingSpinner label="İş piyasası göstergeleri ve beceri trendleri hesaplanıyor..." />;
  if (error) return <ErrorBanner message={error} onRetry={fetchDashboard} />;
  if (!data || data.total_jobs === 0) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold">Analiz Edilmiş İlan Bulunamadı</h2>
          {!includeDemo && (
            <button
              onClick={() => setIncludeDemo(true)}
              className="px-3.5 py-2 rounded-xl text-xs font-semibold bg-brand-teal text-white"
            >
              Sentetik Demo Verilerini Göster
            </button>
          )}
        </div>
        <EmptyState
          title="Veritabanında Gösterilecek İlan Yok"
          description="Analiz sonuçlarını görmek için CSV formatında iş ilanı veri seti yükleyebilir veya sentetik demo veri setini etkinleştirebilirsiniz."
          actionLabel="Veri Yönetimi Sayfasına Git"
          onAction={() => navigate('/datasets')}
        />
      </div>
    );
  }

  const trendSkillKeys = data.top_skills.slice(0, 4).map((s) => s.name);

  return (
    <div className="space-y-6">
      <SyntheticDataBanner demoCount={data.demo_jobs_count} realCount={data.real_jobs_count} />

      {/* Top Controls Bar & İBE Hızlı Akış */}
      <div className="rounded-2xl bg-white dark:bg-navy-900 p-5 border border-slate-200 dark:border-slate-800 shadow-xs space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3 text-xs text-slate-600 dark:text-slate-300">
            <div className="p-2 rounded-xl bg-brand-purple/10 text-brand-purple">
              <Calendar className="h-4 w-4" />
            </div>
            <div>
              <div className="text-[11px] uppercase tracking-wider font-semibold text-slate-400">
                Aktif Veri Penceresi
              </div>
              <strong className="text-sm text-slate-900 dark:text-white tabular-nums">
                {data.date_range.min_date} — {data.date_range.max_date}
              </strong>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            {data.demo_jobs_count > 0 && (
              <label className="inline-flex items-center gap-2 min-h-[44px] px-3 rounded-xl border border-slate-200 dark:border-slate-700 text-xs font-medium cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={includeDemo}
                  onChange={(e) => setIncludeDemo(e.target.checked)}
                  className="rounded border-slate-300 text-brand-purple focus:ring-brand-purple"
                />
                <span>Demo Verisi Dahil ({data.demo_jobs_count})</span>
              </label>
            )}
            <button
              onClick={() => navigate('/market')}
              className="inline-flex items-center gap-1.5 min-h-[44px] px-4 rounded-xl text-xs font-semibold bg-slate-100 dark:bg-navy-800 text-slate-800 dark:text-slate-100 hover:bg-slate-200 dark:hover:bg-navy-700 transition"
            >
              <MapPin className="h-3.5 w-3.5 text-brand-teal" />
              <span>Şehir & Piyasa Filtrele</span>
            </button>
            <button
              onClick={() => navigate('/career')}
              className="inline-flex items-center gap-1.5 min-h-[44px] px-4 rounded-xl text-xs font-semibold bg-brand-purple text-white hover:bg-indigo-600 shadow-xs transition"
            >
              <Briefcase className="h-3.5 w-3.5" />
              <span>CV Analizi & Yol Haritası</span>
            </button>
            <button
              onClick={() => navigate('/datasets')}
              className="inline-flex items-center gap-1.5 min-h-[44px] px-4 rounded-xl text-xs font-semibold bg-brand-purple/10 text-brand-purple dark:bg-brand-purple/20 dark:text-indigo-300 hover:bg-brand-purple hover:text-white transition"
            >
              <span>Veri Yönetimi</span>
              <ArrowUpRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* KPI Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="rounded-2xl bg-white dark:bg-navy-900 p-5 border border-slate-200/80 dark:border-slate-800/80 shadow-xs hover:border-brand-purple/50 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              Toplam Analiz Edilen İlan
            </span>
            <div className="p-2.5 rounded-xl bg-brand-purple/10 text-brand-purple">
              <Briefcase className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-3 text-3xl font-extrabold text-slate-900 dark:text-white tabular-nums">
            {data.total_jobs}
          </div>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            {data.unique_companies} farklı kurum • {data.real_jobs_count} gerçek / {data.demo_jobs_count} demo
          </p>
        </div>

        <div className="rounded-2xl bg-white dark:bg-navy-900 p-5 border border-slate-200/80 dark:border-slate-800/80 shadow-xs hover:border-brand-teal/50 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              Lider Beceri Talebi
            </span>
            <div className="p-2.5 rounded-xl bg-brand-teal/10 text-brand-teal">
              <Sparkles className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-3 text-2xl font-extrabold text-slate-900 dark:text-white">
            {data.top_skills[0]?.name || '-'}
          </div>
          <p className="mt-1 text-xs text-emerald-600 dark:text-emerald-400 font-medium">
            İlanların %{data.top_skills[0]?.percentage || 0} kadarında aranıyor ({data.top_skills[0]?.count || 0} ilan)
          </p>
        </div>

        <div className="rounded-2xl bg-white dark:bg-navy-900 p-5 border border-slate-200/80 dark:border-slate-800/80 shadow-xs hover:border-brand-purple/50 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              Uzaktan & Hibrit Oranı
            </span>
            <div className="p-2.5 rounded-xl bg-indigo-500/10 text-indigo-400">
              <Globe2 className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-3 text-3xl font-extrabold text-slate-900 dark:text-white">%{data.remote_ratio}</div>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Tam Uzaktan %{data.remote_ratio} • Hibrit %{data.hybrid_ratio} • Ofis %{data.onsite_ratio}
          </p>
        </div>

        <div className="rounded-2xl bg-white dark:bg-navy-900 p-5 border border-slate-200/80 dark:border-slate-800/80 shadow-xs hover:border-brand-teal/50 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              Aktif Şehir & Bölge
            </span>
            <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-400">
              <MapPin className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-3 text-3xl font-extrabold text-slate-900 dark:text-white">{data.unique_cities}</div>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            İlk sırada: {data.city_distribution[0]?.city || '-'} ({data.city_distribution[0]?.count || 0} ilan)
          </p>
        </div>
      </div>

      {/* Primary Charts Grid: Top 10 Skills & Top Roles */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Top 10 Skills Bar Chart */}
        <div className="lg:col-span-7 rounded-2xl bg-white dark:bg-navy-900 p-6 border border-slate-200/80 dark:border-slate-800/80 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-bold text-slate-900 dark:text-white">En Çok Aranan 10 Beceri</h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                NLP beceri çıkarım motorunun ilan açıklamalarından tespit ettiği sıklıklar
              </p>
            </div>
            <button
              onClick={() => navigate('/skills')}
              className="text-xs font-semibold text-brand-purple dark:text-brand-teal hover:underline"
            >
              Tümünü Keşfet →
            </button>
          </div>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.top_skills} layout="vertical" margin={{ top: 5, right: 25, left: 25, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.2} />
                <XAxis type="number" tick={{ fontSize: 12, fill: '#94a3b8' }} />
                <YAxis
                  dataKey="name"
                  type="category"
                  width={110}
                  tick={{ fontSize: 12, fill: '#94a3b8', fontWeight: 600 }}
                />
                <Tooltip
                  formatter={(value: any, _name: any, props: any) => [
                    `${value} İlan (%${props.payload.percentage})`,
                    props.payload.category,
                  ]}
                  contentStyle={{
                    backgroundColor: '#0B132B',
                    borderColor: '#334155',
                    borderRadius: '12px',
                    color: '#f8fafc',
                    fontSize: '12px',
                  }}
                />
                <Bar dataKey="count" radius={[0, 8, 8, 0]}>
                  {data.top_skills.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={index % 2 === 0 ? '#6366F1' : '#06B6D4'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Top Roles Distribution */}
        <div className="lg:col-span-5 rounded-2xl bg-white dark:bg-navy-900 p-6 border border-slate-200/80 dark:border-slate-800/80 shadow-xs">
          <div className="mb-4">
            <h2 className="text-base font-bold text-slate-900 dark:text-white">En Çok İlan Bulunan Pozisyonlar</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Normalize edilmiş meslek gruplarına göre ilan yoğunluğu
            </p>
          </div>
          <div className="space-y-3">
            {data.top_roles.map((r, idx) => (
              <div key={r.role} className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-slate-800 dark:text-slate-200">
                    {idx + 1}. {r.role}
                  </span>
                  <span className="text-slate-500 dark:text-slate-400">
                    {r.count} ilan (<strong className="text-brand-teal">%{r.percentage}</strong>)
                  </span>
                </div>
                <div className="w-full h-2.5 rounded-full bg-slate-100 dark:bg-navy-800 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-brand-purple to-brand-teal"
                    style={{ width: `${Math.min(100, Math.max(6, r.percentage * 2.2))}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Second Row Charts: Skill Demand Trends Over Time & Sector + City */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Monthly Skill Trend */}
        <div className="lg:col-span-7 rounded-2xl bg-white dark:bg-navy-900 p-6 border border-slate-200/80 dark:border-slate-800/80 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-brand-teal" />
                <span>Beceri Talep Trendleri (Aylık Değişim)</span>
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                En çok aranan 4 becerinin yayın tarihine göre aylık ilan sıklığı
              </p>
            </div>
            <button
              onClick={() => navigate('/models')}
              className="text-xs font-semibold text-brand-purple dark:text-brand-teal hover:underline"
            >
              ML Tahmin Modeli →
            </button>
          </div>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.skill_trends} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.2} />
                <XAxis dataKey="period" tick={{ fontSize: 12, fill: '#94a3b8' }} />
                <YAxis tick={{ fontSize: 12, fill: '#94a3b8' }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0B132B',
                    borderColor: '#334155',
                    borderRadius: '12px',
                    color: '#f8fafc',
                    fontSize: '12px',
                  }}
                />
                <Legend wrapperStyle={{ fontSize: '12px' }} />
                {trendSkillKeys.map((skillKey, idx) => (
                  <Line
                    key={skillKey}
                    type="monotone"
                    dataKey={skillKey}
                    stroke={CHART_COLORS[idx % CHART_COLORS.length]}
                    strokeWidth={2.5}
                    dot={{ r: 4 }}
                    activeDot={{ r: 6 }}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Sector & City Distribution */}
        <div className="lg:col-span-5 grid grid-cols-1 gap-6">
          <div className="rounded-2xl bg-white dark:bg-navy-900 p-6 border border-slate-200/80 dark:border-slate-800/80 shadow-xs">
            <h2 className="text-base font-bold text-slate-900 dark:text-white mb-1">Sektörlere Göre İlan Dağılımı</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-3">İlanların sektörel kırılımı</p>
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data.sector_distribution}
                    dataKey="count"
                    nameKey="sector"
                    cx="50%"
                    cy="50%"
                    innerRadius={45}
                    outerRadius={78}
                    paddingAngle={3}
                  >
                    {data.sector_distribution.map((_, idx) => (
                      <Cell key={`sec-${idx}`} fill={CHART_COLORS[idx % CHART_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(val: any, name: any) => [`${val} İlan`, name]}
                    contentStyle={{
                      backgroundColor: '#0B132B',
                      borderColor: '#334155',
                      borderRadius: '12px',
                      color: '#f8fafc',
                      fontSize: '12px',
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: '11px' }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>

      {/* City Distribution & Recent Analyzed Jobs */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-5 rounded-2xl bg-white dark:bg-navy-900 p-6 border border-slate-200/80 dark:border-slate-800/80 shadow-xs">
          <h2 className="text-base font-bold text-slate-900 dark:text-white mb-1">Şehir Bazında İş İlanı Dağılımı</h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">Türkiye geneli lokasyon yoğunluğu</p>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.city_distribution} margin={{ top: 5, right: 15, left: 0, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.2} />
                <XAxis dataKey="city" tick={{ fontSize: 11, fill: '#94a3b8' }} angle={-20} textAnchor="end" />
                <YAxis tick={{ fontSize: 12, fill: '#94a3b8' }} />
                <Tooltip
                  formatter={(value: any) => [`${value} İlan`, 'Toplam']}
                  contentStyle={{
                    backgroundColor: '#0B132B',
                    borderColor: '#334155',
                    borderRadius: '12px',
                    color: '#f8fafc',
                    fontSize: '12px',
                  }}
                />
                <Bar dataKey="count" fill="#06B6D4" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Recent Analyzed Jobs Table */}
        <div className="lg:col-span-7 rounded-2xl bg-white dark:bg-navy-900 p-6 border border-slate-200/80 dark:border-slate-800/80 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-bold text-slate-900 dark:text-white">Son Analiz Edilen İlanlar</h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                NLP ile çıkarılan beceriler ve ML sınıflandırma etiketleri
              </p>
            </div>
            <button
              onClick={() => navigate('/market')}
              className="text-xs font-semibold text-brand-purple dark:text-brand-teal hover:underline"
            >
              Detaylı Filtrele →
            </button>
          </div>
          <div className="space-y-3">
            {data.recent_jobs.map((job) => (
              <div
                key={job.id}
                className="p-3.5 rounded-xl border border-slate-200/70 dark:border-slate-800 bg-slate-50/60 dark:bg-navy-950/60 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
              >
                <div className="space-y-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-semibold text-sm text-slate-900 dark:text-white">{job.job_title}</span>
                    {job.predicted_category && (
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-brand-purple/15 text-brand-purple dark:text-indigo-300">
                        {job.predicted_category}
                      </span>
                    )}
                    {job.is_demo && (
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-600 dark:text-amber-300 font-medium">
                        Sentetik Demo
                      </span>
                    )}
                  </div>
                  <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500 dark:text-slate-400">
                    <span className="inline-flex items-center gap-1">
                      <Building2 className="h-3.5 w-3.5" /> {job.company_name}
                    </span>
                    <span className="inline-flex items-center gap-1">
                      <MapPin className="h-3.5 w-3.5" /> {job.location} ({job.remote_type})
                    </span>
                    <span>{job.posted_date}</span>
                  </div>
                </div>
                <div className="flex flex-wrap gap-1.5 sm:justify-end max-w-xs">
                  {job.skills.slice(0, 5).map((sk) => (
                    <button
                      key={sk}
                      onClick={() => navigate(`/skills?skill=${encodeURIComponent(sk)}`)}
                      className="text-[11px] font-medium px-2 py-0.5 rounded-md bg-slate-200/80 dark:bg-navy-800 text-slate-700 dark:text-slate-200 hover:bg-brand-teal hover:text-white transition"
                    >
                      {sk}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
