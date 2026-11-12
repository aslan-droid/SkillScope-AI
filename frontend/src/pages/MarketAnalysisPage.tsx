import React, { useEffect, useState } from 'react';
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
import { ExternalLink, Filter, MapPin, RotateCcw, Wallet } from 'lucide-react';
import { api } from '../services/api';
import type { JobSummaryItem, MarketAnalytics } from '../types';
import { EmptyState, ErrorBanner, LoadingSpinner } from '../components/StatusUI';

const COLORS = ['#2563EB', '#0D9488', '#4F46E5', '#059669', '#D97706', '#DC2626', '#0284C7'];

export const MarketAnalysisPage: React.FC = () => {
  const [city, setCity] = useState('Tümü');
  const [role, setRole] = useState('Tümü');
  const [sector, setSector] = useState('Tümü');
  const [skill, setSkill] = useState('Tümü');
  const [remoteType, setRemoteType] = useState('Tümü');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [includeDemo, setIncludeDemo] = useState(true);
  const [jobPage, setJobPage] = useState(1);

  const [data, setData] = useState<MarketAnalytics | null>(null);
  const [jobsList, setJobsList] = useState<{ total: number; items: JobSummaryItem[] }>({
    total: 0,
    items: [],
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadMarketData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [res, jobsRes] = await Promise.all([
        api.getMarketAnalytics({
          city,
          role,
          sector,
          skill,
          remote_type: remoteType,
          date_from: dateFrom || undefined,
          date_to: dateTo || undefined,
          include_demo: includeDemo,
        }),
        api.listJobs({
          city,
          role,
          sector,
          skill,
          remote_type: remoteType,
          include_demo: includeDemo,
          page: jobPage,
          page_size: 12,
        }),
      ]);
      setData(res);
      setJobsList({ total: jobsRes.total, items: jobsRes.items });
    } catch (err: any) {
      setError(err.message || 'İş piyasası analiz verileri alınamadı.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setJobPage(1);
  }, [city, role, sector, skill, remoteType, dateFrom, dateTo, includeDemo]);

  useEffect(() => {
    loadMarketData();
  }, [city, role, sector, skill, remoteType, dateFrom, dateTo, includeDemo, jobPage]);

  const resetFilters = () => {
    setCity('Tümü');
    setRole('Tümü');
    setSector('Tümü');
    setSkill('Tümü');
    setRemoteType('Tümü');
    setDateFrom('');
    setDateTo('');
    setIncludeDemo(true);
  };

  if (loading && !data) return <LoadingSpinner label="İş piyasası çok boyutlu filtreleri hesaplanıyor..." />;
  if (error) return <ErrorBanner message={error} onRetry={loadMarketData} />;
  if (!data) return null;

  const trendSkills = data.top_skills.slice(0, 4).map((s) => s.name);

  return (
    <div className="space-y-6">
      {/* Filter Bar */}
      <div className="rounded-2xl bg-white dark:bg-navy-900 p-5 border border-slate-200/80 dark:border-slate-800/80 shadow-xs space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2 text-sm font-bold text-slate-900 dark:text-white">
            <Filter className="h-4 w-4 text-brand-purple" />
            <span>Çok Boyutlu Piyasa Filtreleri</span>
            <span className="ml-2 text-xs font-semibold px-2.5 py-0.5 rounded-full bg-brand-teal/15 text-brand-teal">
              {data.sample_size} İlan Eşleşti
            </span>
          </div>
          <button
            onClick={resetFilters}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-navy-800 transition"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            <span>Filtreleri Sıfırla</span>
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          <div>
            <label className="block text-[11px] font-semibold text-slate-500 dark:text-slate-400 mb-1">Şehir</label>
            <select
              value={city}
              onChange={(e) => setCity(e.target.value)}
              className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-navy-950 px-3 py-2 text-xs"
            >
              <option value="Tümü">Tüm Şehirler</option>
              {data.filters_available.cities.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-500 dark:text-slate-400 mb-1">Pozisyon</label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-navy-950 px-3 py-2 text-xs"
            >
              <option value="Tümü">Tüm Pozisyonlar</option>
              {data.filters_available.roles.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-500 dark:text-slate-400 mb-1">Sektör</label>
            <select
              value={sector}
              onChange={(e) => setSector(e.target.value)}
              className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-navy-950 px-3 py-2 text-xs"
            >
              <option value="Tümü">Tüm Sektörler</option>
              {data.filters_available.sectors.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-500 dark:text-slate-400 mb-1">Beceri</label>
            <select
              value={skill}
              onChange={(e) => setSkill(e.target.value)}
              className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-navy-950 px-3 py-2 text-xs"
            >
              <option value="Tümü">Tüm Beceriler</option>
              {data.filters_available.skills.map((sk) => (
                <option key={sk} value={sk}>
                  {sk}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-500 dark:text-slate-400 mb-1">
              Çalışma Şekli
            </label>
            <select
              value={remoteType}
              onChange={(e) => setRemoteType(e.target.value)}
              className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-navy-950 px-3 py-2 text-xs"
            >
              <option value="Tümü">Tümü</option>
              {data.filters_available.remote_types.map((rt) => (
                <option key={rt} value={rt}>
                  {rt}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-500 dark:text-slate-400 mb-1">
              Başlangıç Tarihi
            </label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-navy-950 px-3 py-1.5 text-xs"
            />
          </div>
        </div>
      </div>

      {data.sample_size === 0 ? (
        <EmptyState
          title="Seçilen Filtrelerle Eşleşen İlan Bulunamadı"
          description="Farklı bir şehir, pozisyon veya beceri kombinasyonu deneyebilirsiniz."
          actionLabel="Filtreleri Sıfırla"
          onAction={resetFilters}
        />
      ) : (
        <>
          {/* Row 1: Top Skills & Role Distribution */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="rounded-2xl bg-white dark:bg-navy-900 p-6 border border-slate-200/80 dark:border-slate-800/80 shadow-xs">
              <h3 className="text-base font-bold text-slate-900 dark:text-white mb-1">
                Filtrelenen İlanlarda En Çok Aranan Beceriler
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">
                Seçili örneklem ({data.sample_size} ilan) içindeki beceri sıklığı
              </p>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={data.top_skills.slice(0, 10)}
                    layout="vertical"
                    margin={{ top: 5, right: 20, left: 25, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.2} />
                    <XAxis type="number" tick={{ fontSize: 12, fill: '#94a3b8' }} />
                    <YAxis dataKey="name" type="category" width={110} tick={{ fontSize: 12, fill: '#94a3b8' }} />
                    <Tooltip
                      formatter={(val: any, _n: any, p: any) => [`${val} İlan (%${p.payload.percentage})`, 'Talep']}
                      contentStyle={{
                        backgroundColor: '#0B132B',
                        borderColor: '#334155',
                        borderRadius: '12px',
                        color: '#f8fafc',
                        fontSize: '12px',
                      }}
                    />
                    <Bar dataKey="count" fill="#6366F1" radius={[0, 8, 8, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="rounded-2xl bg-white dark:bg-navy-900 p-6 border border-slate-200/80 dark:border-slate-800/80 shadow-xs">
              <h3 className="text-base font-bold text-slate-900 dark:text-white mb-1">Pozisyon Dağılımı</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">
                Meslek gruplarının seçili kesitteki ağırlığı
              </p>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.role_distribution} margin={{ top: 5, right: 15, left: 0, bottom: 45 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.2} />
                    <XAxis
                      dataKey="role"
                      tick={{ fontSize: 11, fill: '#94a3b8' }}
                      angle={-25}
                      textAnchor="end"
                      interval={0}
                    />
                    <YAxis tick={{ fontSize: 12, fill: '#94a3b8' }} />
                    <Tooltip
                      formatter={(val: any) => [`${val} İlan`, 'Sayı']}
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
          </div>

          {/* Row 2: City Comparison & Sector Distribution */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="rounded-2xl bg-white dark:bg-navy-900 p-6 border border-slate-200/80 dark:border-slate-800/80 shadow-xs">
              <h3 className="text-base font-bold text-slate-900 dark:text-white mb-1">Şehir Karşılaştırması</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">Şehir bazlı ilan sayıları ve oranları</p>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.city_comparison} margin={{ top: 5, right: 15, left: 0, bottom: 25 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.2} />
                    <XAxis dataKey="city" tick={{ fontSize: 12, fill: '#94a3b8' }} />
                    <YAxis tick={{ fontSize: 12, fill: '#94a3b8' }} />
                    <Tooltip
                      formatter={(val: any, _n: any, p: any) => [`${val} İlan (%${p.payload.percentage})`, 'Şehir']}
                      contentStyle={{
                        backgroundColor: '#0B132B',
                        borderColor: '#334155',
                        borderRadius: '12px',
                        color: '#f8fafc',
                        fontSize: '12px',
                      }}
                    />
                    <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                      {data.city_comparison.map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="rounded-2xl bg-white dark:bg-navy-900 p-6 border border-slate-200/80 dark:border-slate-800/80 shadow-xs">
              <h3 className="text-base font-bold text-slate-900 dark:text-white mb-1">Sektör Dağılımı</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">İlanların faaliyet alanlarına göre payı</p>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={data.sector_distribution}
                      dataKey="count"
                      nameKey="sector"
                      cx="50%"
                      cy="50%"
                      innerRadius={55}
                      outerRadius={90}
                      paddingAngle={3}
                    >
                      {data.sector_distribution.map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Pie>
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
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Row 3: Salary Distribution & Skill Trends Over Time */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="rounded-2xl bg-white dark:bg-navy-900 p-6 border border-slate-200/80 dark:border-slate-800/80 shadow-xs">
              <div className="flex items-center gap-2 mb-1">
                <Wallet className="h-4 w-4 text-brand-teal" />
                <h3 className="text-base font-bold text-slate-900 dark:text-white">
                  Pozisyon Bazlı Maaş Dağılımı (TRY)
                </h3>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">
                Yalnızca yeterli ve doğrulanmış maaş aralığı bulunan pozisyonlar gösterilir
              </p>

              {!data.salary_analytics.sufficient_data ? (
                <div className="p-6 rounded-xl bg-slate-100/70 dark:bg-navy-950/70 border border-slate-200 dark:border-slate-800 text-xs text-slate-600 dark:text-slate-300">
                  {data.salary_analytics.reason ||
                    'Seçili filtrelerde güvenilir maaş istatistiği için yeterli örneklem bulunmuyor.'}
                </div>
              ) : (
                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={data.salary_analytics.by_role}
                      margin={{ top: 5, right: 20, left: 10, bottom: 45 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.2} />
                      <XAxis
                        dataKey="role"
                        tick={{ fontSize: 10, fill: '#94a3b8' }}
                        angle={-25}
                        textAnchor="end"
                        interval={0}
                      />
                      <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} />
                      <Tooltip
                        formatter={(val: any) => [`${Number(val).toLocaleString('tr-TR')} ₺`]}
                        contentStyle={{
                          backgroundColor: '#0B132B',
                          borderColor: '#334155',
                          borderRadius: '12px',
                          color: '#f8fafc',
                          fontSize: '12px',
                        }}
                      />
                      <Legend wrapperStyle={{ fontSize: '11px' }} />
                      <Bar dataKey="avg_min" name="Ort. Alt Maaş" fill="#06B6D4" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="avg_max" name="Ort. Üst Maaş" fill="#6366F1" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>

            <div className="rounded-2xl bg-white dark:bg-navy-900 p-6 border border-slate-200/80 dark:border-slate-800/80 shadow-xs">
              <h3 className="text-base font-bold text-slate-900 dark:text-white mb-1">
                Zaman İçindeki Beceri Değişimleri
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">
                Seçili kesitteki en popüler becerilerin aylık talep eğrisi
              </p>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={data.skill_trends} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
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
                    {trendSkills.map((skName, idx) => (
                      <Line
                        key={skName}
                        type="monotone"
                        dataKey={skName}
                        stroke={COLORS[idx % COLORS.length]}
                        strokeWidth={2.5}
                        dot={{ r: 3.5 }}
                      />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Clickable Real Job Listings */}
          <div className="rounded-2xl bg-white dark:bg-navy-900 p-6 border border-slate-200 dark:border-slate-800 shadow-xs space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 dark:border-slate-800 pb-4">
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white">
                  Filtrelenen İş İlanları ve Başvuru Bağlantıları ({jobsList.total} İlan)
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Seçili şehir, pozisyon ve beceri kriterlerine uyan ilanları doğrudan kaynağında inceleyebilirsiniz.
                </p>
              </div>
              <div className="flex items-center gap-2 text-xs">
                <button
                  type="button"
                  disabled={jobPage <= 1}
                  onClick={() => setJobPage((p) => Math.max(1, p - 1))}
                  className="min-h-[40px] px-3.5 rounded-xl border border-slate-200 dark:border-slate-700 font-semibold disabled:opacity-40 hover:bg-slate-100 dark:hover:bg-navy-800 transition"
                >
                  Önceki
                </button>
                <span className="px-2 font-mono text-slate-600 dark:text-slate-300 tabular-nums">
                  Sayfa {jobPage} / {Math.max(1, Math.ceil(jobsList.total / 12))}
                </span>
                <button
                  type="button"
                  disabled={jobPage * 12 >= jobsList.total}
                  onClick={() => setJobPage((p) => p + 1)}
                  className="min-h-[40px] px-3.5 rounded-xl border border-slate-200 dark:border-slate-700 font-semibold disabled:opacity-40 hover:bg-slate-100 dark:hover:bg-navy-800 transition"
                >
                  Sonraki
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
              {jobsList.items.map((job) => (
                <div
                  key={job.id}
                  className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-navy-950/60 flex flex-col justify-between gap-3"
                >
                  <div className="space-y-1.5">
                    <div className="flex items-start justify-between gap-2">
                      <h4 className="text-sm font-bold text-slate-900 dark:text-white leading-snug">
                        {job.job_title}
                      </h4>
                      <span className="shrink-0 px-2 py-0.5 rounded-md text-[10px] font-semibold bg-slate-200/80 dark:bg-navy-800 text-slate-700 dark:text-slate-300">
                        {job.remote_type}
                      </span>
                    </div>
                    <div className="flex flex-wrap items-center gap-2 text-xs text-slate-600 dark:text-slate-400">
                      <span className="font-semibold text-slate-800 dark:text-slate-200">{job.company_name}</span>
                      <span>•</span>
                      <span className="inline-flex items-center gap-1">
                        <MapPin className="h-3.5 w-3.5 text-brand-teal" />
                        {job.location}
                      </span>
                      <span>•</span>
                      <span className="tabular-nums">{job.posted_date}</span>
                    </div>
                    {job.skills.length > 0 && (
                      <div className="flex flex-wrap gap-1 pt-1">
                        {job.skills.slice(0, 5).map((sk) => (
                          <span
                            key={sk}
                            className="px-2 py-0.5 rounded-md text-[11px] font-medium bg-blue-500/10 text-blue-700 dark:text-blue-300"
                          >
                            {sk}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="flex items-center justify-between pt-2 border-t border-slate-200/70 dark:border-slate-800/70">
                    <span className="text-[11px] text-slate-500 dark:text-slate-400 truncate">
                      {job.source_name || job.sector}
                    </span>
                    {job.source_url ? (
                      <a
                        href={job.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1.5 min-h-[36px] px-3 rounded-lg bg-brand-purple text-white text-xs font-semibold hover:bg-blue-700 transition shrink-0"
                      >
                        <span>İlana Git</span>
                        <ExternalLink className="h-3.5 w-3.5" />
                      </a>
                    ) : (
                      <span className="text-[11px] text-slate-400">Bağlantı yok</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
};
