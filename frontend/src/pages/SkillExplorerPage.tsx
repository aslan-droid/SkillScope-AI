import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { BookOpen, Compass, ExternalLink, Layers, Network, TrendingUp } from 'lucide-react';
import { api } from '../services/api';
import type { SkillCatalogItem, SkillDeepDive } from '../types';
import { ErrorBanner, LoadingSpinner } from '../components/StatusUI';

export const SkillExplorerPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialSkill = searchParams.get('skill') || 'SQL';

  const [skillsCatalog, setSkillsCatalog] = useState<SkillCatalogItem[]>([]);
  const [selectedSkill, setSelectedSkill] = useState(initialSkill);
  const [categoryFilter, setCategoryFilter] = useState('Tümü');
  const [deepDive, setDeepDive] = useState<SkillDeepDive | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listSkills()
      .then((res) => setSkillsCatalog(res.items))
      .catch(() => {});
  }, []);

  const loadSkillDetail = async (skillIdent: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getSkillDeepDive(skillIdent, true);
      setDeepDive(res);
    } catch (err: any) {
      setError(err.message || 'Beceri analizi yüklenemedi.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSkillDetail(selectedSkill);
    setSearchParams({ skill: selectedSkill }, { replace: true });
  }, [selectedSkill]);

  const categories = ['Tümü', ...Array.from(new Set(skillsCatalog.map((s) => s.category)))];
  const filteredSkills =
    categoryFilter === 'Tümü'
      ? skillsCatalog
      : skillsCatalog.filter((s) => s.category === categoryFilter);

  return (
    <div className="space-y-6">
      {/* Top Skill Selector Bar */}
      <div className="rounded-2xl bg-white dark:bg-navy-900 p-5 border border-slate-200/80 dark:border-slate-800/80 shadow-xs space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <Compass className="h-5 w-5 text-brand-teal" />
            <div>
              <h2 className="text-sm font-bold text-slate-900 dark:text-white">
                Beceri Keşif ve Birliktelik (Co-Occurrence) Motoru
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Bir teknoloji seçerek hangi becerilerle birlikte arandığını, pozisyon ve sektör talebini inceleyin
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 dark:text-slate-400">Kategori:</span>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-navy-950 px-3 py-1.5 text-xs font-medium"
            >
              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Pill buttons for quick skill selection */}
        <div className="flex flex-wrap gap-2 max-h-36 overflow-y-auto pt-1">
          {filteredSkills.map((sk) => {
            const active =
              sk.name.toLowerCase() === selectedSkill.toLowerCase() ||
              sk.slug.toLowerCase() === selectedSkill.toLowerCase();
            return (
              <button
                key={sk.id}
                onClick={() => setSelectedSkill(sk.name)}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition flex items-center gap-1.5 ${
                  active
                    ? 'bg-gradient-to-r from-brand-purple to-brand-teal text-white shadow-sm'
                    : 'bg-slate-100 dark:bg-navy-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-navy-700'
                }`}
              >
                <span>{sk.name}</span>
                <span
                  className={`text-[10px] px-1.5 py-0.2 rounded-full ${
                    active ? 'bg-white/20 text-white' : 'bg-slate-200 dark:bg-navy-950 text-slate-500'
                  }`}
                >
                  {sk.demand_count}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {loading ? (
        <LoadingSpinner label={`'${selectedSkill}' becerisi için birliktelik ve trend analizleri hesaplanıyor...`} />
      ) : error ? (
        <ErrorBanner message={error} onRetry={() => loadSkillDetail(selectedSkill)} />
      ) : deepDive ? (
        <>
          {/* Skill Hero Summary */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <div className="lg:col-span-8 rounded-2xl bg-white dark:bg-navy-900 p-6 border border-slate-200/80 dark:border-slate-800/80 shadow-xs space-y-4">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2.5">
                    <h2 className="text-2xl font-extrabold text-slate-900 dark:text-white">
                      {deepDive.skill.name}
                    </h2>
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-brand-purple/15 text-brand-purple dark:text-indigo-300">
                      {deepDive.skill.category}
                    </span>
                  </div>
                  <p className="mt-1.5 text-sm text-slate-600 dark:text-slate-300">
                    {deepDive.skill.description}
                  </p>
                </div>

                <div className="text-right bg-slate-50 dark:bg-navy-950 px-4 py-3 rounded-xl border border-slate-200/70 dark:border-slate-800">
                  <div className="text-2xl font-extrabold text-brand-teal">
                    {deepDive.demand_count} İlan (%{deepDive.demand_percentage})
                  </div>
                  <div className="text-[11px] text-slate-500 dark:text-slate-400">
                    Toplam {deepDive.total_jobs_analyzed} analiz edilen ilan içinde
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 border-t border-slate-200/70 dark:border-slate-800 text-xs">
                <div>
                  <span className="text-slate-500 dark:text-slate-400 block">Eş Anlamlı / Alternatif Yazımlar:</span>
                  <span className="font-semibold text-slate-800 dark:text-slate-200">
                    {deepDive.skill.aliases.length > 0 ? deepDive.skill.aliases.join(', ') : 'Standart Terim'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 dark:text-slate-400 block">Önerilen Önkoşul Beceriler:</span>
                  <span className="font-semibold text-slate-800 dark:text-slate-200">
                    {deepDive.skill.prerequisites.length > 0
                      ? deepDive.skill.prerequisites.join(', ')
                      : 'Temel seviye (Önkoşulsuz)'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 dark:text-slate-400 block">Tahmini Öğrenme Süresi:</span>
                  <span className="font-semibold text-brand-purple dark:text-indigo-300">
                    ~{deepDive.skill.estimated_hours} Saat Odaklı Çalışma
                  </span>
                </div>
              </div>
            </div>

            {/* Free Learning Resources Card */}
            <div className="lg:col-span-4 rounded-2xl bg-white dark:bg-navy-900 p-6 border border-slate-200/80 dark:border-slate-800/80 shadow-xs space-y-3">
              <div className="flex items-center gap-2 text-sm font-bold text-slate-900 dark:text-white">
                <BookOpen className="h-4 w-4 text-brand-teal" />
                <span>Ücretsiz Öğrenme Kaynakları</span>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Sıfır bütçe kuralına uygun açık erişimli eğitim ve dokümantasyonlar:
              </p>
              <div className="space-y-2">
                {deepDive.skill.learning_resources.map((res, i) => (
                  <a
                    key={i}
                    href={res.url}
                    target="_blank"
                    rel="noreferrer"
                    className="block p-3 rounded-xl border border-slate-200 dark:border-slate-800 hover:border-brand-teal bg-slate-50/70 dark:bg-navy-950/70 transition group"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-xs font-semibold text-slate-800 dark:text-slate-100 group-hover:text-brand-teal">
                        {res.title}
                      </span>
                      <ExternalLink className="h-3.5 w-3.5 shrink-0 text-slate-400 group-hover:text-brand-teal" />
                    </div>
                    <span className="text-[10px] text-brand-purple dark:text-indigo-300 font-medium">{res.type}</span>
                  </a>
                ))}
              </div>
            </div>
          </div>

          {/* Co-occurring Skills & Demand by Role */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="rounded-2xl bg-white dark:bg-navy-900 p-6 border border-slate-200/80 dark:border-slate-800/80 shadow-xs">
              <div className="flex items-center gap-2 mb-1">
                <Network className="h-4 w-4 text-brand-purple" />
                <h3 className="text-base font-bold text-slate-900 dark:text-white">
                  {deepDive.skill.name} İle Birlikte En Çok Aranan Beceriler
                </h3>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">
                Aynı iş ilanında {deepDive.skill.name} ile beraber geçen tamamlayıcı yetkinlikler
              </p>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={deepDive.co_occurring_skills}
                    layout="vertical"
                    margin={{ top: 5, right: 20, left: 25, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.2} />
                    <XAxis type="number" tick={{ fontSize: 12, fill: '#94a3b8' }} />
                    <YAxis dataKey="name" type="category" width={115} tick={{ fontSize: 12, fill: '#94a3b8' }} />
                    <Tooltip
                      formatter={(val: any, _n: any, p: any) => [
                        `${val} Ortak İlan (%${p.payload.co_percentage})`,
                        p.payload.category,
                      ]}
                      contentStyle={{
                        backgroundColor: '#0B132B',
                        borderColor: '#334155',
                        borderRadius: '12px',
                        color: '#f8fafc',
                        fontSize: '12px',
                      }}
                    />
                    <Bar dataKey="co_count" fill="#06B6D4" radius={[0, 8, 8, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="rounded-2xl bg-white dark:bg-navy-900 p-6 border border-slate-200/80 dark:border-slate-800/80 shadow-xs">
              <div className="flex items-center gap-2 mb-1">
                <Layers className="h-4 w-4 text-brand-teal" />
                <h3 className="text-base font-bold text-slate-900 dark:text-white">
                  Pozisyonlara Göre {deepDive.skill.name} Talebi
                </h3>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">
                Bu beceriyi en çok talep eden meslek grupları
              </p>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={deepDive.by_role} margin={{ top: 5, right: 15, left: 0, bottom: 45 }}>
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
                      formatter={(val: any, _n: any, p: any) => [`${val} İlan (%${p.payload.percentage})`, 'Pozisyon']}
                      contentStyle={{
                        backgroundColor: '#0B132B',
                        borderColor: '#334155',
                        borderRadius: '12px',
                        color: '#f8fafc',
                        fontSize: '12px',
                      }}
                    />
                    <Bar dataKey="count" fill="#6366F1" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Sector Breakdown & Monthly Trend */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="rounded-2xl bg-white dark:bg-navy-900 p-6 border border-slate-200/80 dark:border-slate-800/80 shadow-xs">
              <h3 className="text-base font-bold text-slate-900 dark:text-white mb-1">
                Sektörlere Göre {deepDive.skill.name} Dağılımı
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">Hangi sektörlerde daha yoğun aranıyor?</p>
              <div className="space-y-3">
                {deepDive.by_sector.map((sec) => (
                  <div key={sec.sector} className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className="font-semibold text-slate-800 dark:text-slate-200">{sec.sector}</span>
                      <span className="text-slate-500 dark:text-slate-400">
                        {sec.count} ilan (<strong>%{sec.percentage}</strong>)
                      </span>
                    </div>
                    <div className="w-full h-2.5 rounded-full bg-slate-100 dark:bg-navy-800 overflow-hidden">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-brand-teal to-brand-purple"
                        style={{ width: `${Math.min(100, Math.max(6, sec.percentage))}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-2xl bg-white dark:bg-navy-900 p-6 border border-slate-200/80 dark:border-slate-800/80 shadow-xs">
              <div className="flex items-center gap-2 mb-1">
                <TrendingUp className="h-4 w-4 text-brand-teal" />
                <h3 className="text-base font-bold text-slate-900 dark:text-white">
                  Zaman İçindeki {deepDive.skill.name} Talep Değişimi
                </h3>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">Aylık ilan sıklığı eğrisi</p>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={deepDive.monthly_trend} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
                    <defs>
                      <linearGradient id="skillAreaGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#06B6D4" stopOpacity={0.5} />
                        <stop offset="95%" stopColor="#6366F1" stopOpacity={0.05} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.2} />
                    <XAxis dataKey="period" tick={{ fontSize: 12, fill: '#94a3b8' }} />
                    <YAxis tick={{ fontSize: 12, fill: '#94a3b8' }} />
                    <Tooltip
                      formatter={(val: any) => [`${val} İlan`, deepDive.skill.name]}
                      contentStyle={{
                        backgroundColor: '#0B132B',
                        borderColor: '#334155',
                        borderRadius: '12px',
                        color: '#f8fafc',
                        fontSize: '12px',
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="count"
                      stroke="#06B6D4"
                      strokeWidth={2.5}
                      fillOpacity={1}
                      fill="url(#skillAreaGrad)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
};
