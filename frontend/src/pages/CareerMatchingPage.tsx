import React, { useEffect, useState } from 'react';
import {
  Award,
  BookOpen,
  CheckCircle2,
  Clock,
  ExternalLink,
  FileText,
  GraduationCap,
  Map,
  ShieldCheck,
  Sparkles,
  Trash2,
  Upload,
} from 'lucide-react';
import { api } from '../services/api';
import type { CareerRoadmapResponse, CVAnalysisResult, SkillCatalogItem } from '../types';
import { ErrorBanner, LoadingSpinner, SuccessBanner } from '../components/StatusUI';

const TARGET_ROLES = [
  'Veri Analisti',
  'Veri Bilimci',
  'Yapay Zekâ / ML Mühendisi',
  'Backend Geliştirici',
  'Full-Stack / Yazılım Mühendisi',
  'DevOps & Sistem Mühendisi',
  'Siber Güvenlik Uzmanı',
  'İş Analisti / Ürün Yöneticisi',
];

const LEVELS = ['Öğrenci / Başlangıç', 'Yeni Mezun', 'Junior (1-2 Yıl)', 'Orta Seviye (Mid-Level)'];

export const CareerMatchingPage: React.FC = () => {
  const [targetRole, setTargetRole] = useState('Veri Analisti');
  const [currentLevel, setCurrentLevel] = useState('Yeni Mezun');
  const [weeklyHours, setWeeklyHours] = useState(12);
  const [selectedSkills, setSelectedSkills] = useState<string[]>(['Excel', 'SQL']);
  const [allSkills, setAllSkills] = useState<SkillCatalogItem[]>([]);

  const [cvFile, setCvFile] = useState<File | null>(null);
  const [analysisResult, setAnalysisResult] = useState<CVAnalysisResult | null>(null);
  const [roadmap, setRoadmap] = useState<CareerRoadmapResponse | null>(null);

  const [loadingCV, setLoadingCV] = useState(false);
  const [loadingRoadmap, setLoadingRoadmap] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    api
      .listSkills()
      .then((res) => setAllSkills(res.items))
      .catch(() => {});
  }, []);

  const toggleSkill = (name: string) => {
    setSelectedSkills((prev) => (prev.includes(name) ? prev.filter((s) => s !== name) : [...prev, name]));
  };

  const handleAnalyzeCV = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!cvFile) {
      setError('Lütfen analiz etmek için PDF formatında bir CV dosyası seçin.');
      return;
    }
    setLoadingCV(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const res = await api.analyzeCV(cvFile, targetRole);
      setAnalysisResult(res);
      if (res.extracted_skills.length > 0) {
        setSelectedSkills(res.extracted_skills);
      }
      setSuccessMsg(`'${res.filename}' başarıyla analiz edildi ve '${res.target_role}' ilanlarıyla karşılaştırıldı.`);
    } catch (err: any) {
      setError(err.message || 'CV analizi sırasında hata oluştu.');
    } finally {
      setLoadingCV(false);
    }
  };

  const handleManualMatch = async () => {
    setLoadingCV(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const res = await api.matchCareerSkills({
        target_role: targetRole,
        current_skills: selectedSkills,
        current_level: currentLevel,
      });
      setAnalysisResult(res);
    } catch (err: any) {
      setError(err.message || 'Beceri eşleştirmesi yapılamadı.');
    } finally {
      setLoadingCV(false);
    }
  };

  const handleGenerateRoadmap = async () => {
    setLoadingRoadmap(true);
    setError(null);
    try {
      const res = await api.generateRoadmap({
        target_role: targetRole,
        current_level: currentLevel,
        current_skills: selectedSkills,
        weekly_hours: weeklyHours,
      });
      setRoadmap(res);
    } catch (err: any) {
      setError(err.message || 'Yol haritası oluşturulamadı.');
    } finally {
      setLoadingRoadmap(false);
    }
  };

  const handleDeleteAnalysis = async () => {
    if (!analysisResult?.analysis_id) {
      setAnalysisResult(null);
      return;
    }
    try {
      const res = await api.deleteCVAnalysis(analysisResult.analysis_id);
      setAnalysisResult(null);
      setSuccessMsg(res.message);
    } catch (err: any) {
      setError(err.message || 'Kayıt silinemedi.');
    }
  };

  return (
    <div className="space-y-6">
      {error && <ErrorBanner message={error} onRetry={() => setError(null)} />}
      {successMsg && <SuccessBanner message={successMsg} onClose={() => setSuccessMsg(null)} />}

      {/* Privacy Notice Banner */}
      <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-xs text-emerald-900 dark:text-emerald-200 flex items-center gap-3">
        <ShieldCheck className="h-5 w-5 shrink-0 text-emerald-500" />
        <span>
          <strong>Kişisel Veri ve CV Gizliliği:</strong> Yüklediğiniz PDF CV dosyaları sunucu diskine kalıcı olarak
          kaydedilmez, bellekte işlenir, uygulama loglarına yazılmaz ve hiçbir harici LLM servisine gönderilmez.
        </span>
      </div>

      {/* Top Configuration Grid: PDF CV Upload & Profile / Role Selection */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: PDF CV Upload Card */}
        <form
          onSubmit={handleAnalyzeCV}
          className="lg:col-span-5 rounded-2xl bg-white dark:bg-navy-900 p-6 border border-slate-200/80 dark:border-slate-800/80 shadow-xs flex flex-col justify-between space-y-4"
        >
          <div className="space-y-3">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-xl bg-brand-purple/15 text-brand-purple">
                <FileText className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-base font-bold text-slate-900 dark:text-white">PDF CV Analiz Modülü</h2>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Eğitim, deneyim ve teknik becerilerinizi otomatik çıkarın
                </p>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                Hedeflediğiniz Meslek / Pozisyon
              </label>
              <select
                value={targetRole}
                onChange={(e) => setTargetRole(e.target.value)}
                className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-navy-950 px-3.5 py-2.5 text-xs font-semibold"
              >
                {TARGET_ROLES.map((r) => (
                  <option key={r} value={r}>
                    {r}
                  </option>
                ))}
              </select>
            </div>

            <label className="block border-2 border-dashed border-slate-300 dark:border-slate-700 hover:border-brand-purple rounded-2xl p-5 text-center cursor-pointer transition bg-slate-50/50 dark:bg-navy-950/50">
              <Upload className="h-7 w-7 mx-auto text-brand-teal mb-2" />
              <span className="text-xs font-semibold text-slate-800 dark:text-slate-200 block">
                {cvFile ? cvFile.name : 'PDF Formatında CV Dosyanızı Seçin (Maks. 5 MB)'}
              </span>
              <span className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5 block">
                Yalnızca .pdf uzantılı dosyalar kabul edilir
              </span>
              <input
                type="file"
                accept=".pdf,application/pdf"
                onChange={(e) => setCvFile(e.target.files?.[0] || null)}
                className="hidden"
              />
            </label>
          </div>

          <button
            type="submit"
            disabled={loadingCV}
            className="w-full py-2.5 px-4 rounded-xl text-xs font-bold bg-gradient-to-r from-brand-purple to-indigo-600 text-white hover:opacity-95 transition shadow-md disabled:opacity-50"
          >
            {loadingCV ? 'CV Analiz Ediliyor...' : 'CV Yükle ve Hedef Pozisyonla Eşleştir'}
          </button>
        </form>

        {/* Right: Manual Skill Selection & Roadmap Generator */}
        <div className="lg:col-span-7 rounded-2xl bg-white dark:bg-navy-900 p-6 border border-slate-200/80 dark:border-slate-800/80 shadow-xs space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h2 className="text-base font-bold text-slate-900 dark:text-white">
                Kariyer Profili ve Kişisel Yol Haritası Oluşturucu
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Mevcut seviyenizi, bildiğiniz teknolojileri ve haftalık çalışma sürenizi belirleyin
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block text-[11px] font-semibold text-slate-500 dark:text-slate-400 mb-1">
                Mevcut Seviyeniz
              </label>
              <select
                value={currentLevel}
                onChange={(e) => setCurrentLevel(e.target.value)}
                className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-navy-950 px-3 py-2 text-xs font-medium"
              >
                {LEVELS.map((lv) => (
                  <option key={lv} value={lv}>
                    {lv}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-500 dark:text-slate-400 mb-1">
                Hedef Meslek
              </label>
              <select
                value={targetRole}
                onChange={(e) => setTargetRole(e.target.value)}
                className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-navy-950 px-3 py-2 text-xs font-medium"
              >
                {TARGET_ROLES.map((r) => (
                  <option key={r} value={r}>
                    {r}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-500 dark:text-slate-400 mb-1">
                Haftalık Öğrenme Süresi ({weeklyHours} Saat)
              </label>
              <input
                type="range"
                min={4}
                max={40}
                step={2}
                value={weeklyHours}
                onChange={(e) => setWeeklyHours(Number(e.target.value))}
                className="w-full accent-brand-teal mt-2"
              />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between text-xs mb-2">
              <span className="font-semibold text-slate-700 dark:text-slate-300">
                Mevcut Becerileriniz ({selectedSkills.length} seçili):
              </span>
              <button
                type="button"
                onClick={() => setSelectedSkills([])}
                className="text-[11px] text-slate-400 hover:text-rose-400"
              >
                Seçimi Temizle
              </button>
            </div>
            <div className="flex flex-wrap gap-1.5 max-h-32 overflow-y-auto p-2.5 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200/70 dark:border-slate-800">
              {allSkills.map((sk) => {
                const isSelected = selectedSkills.includes(sk.name);
                return (
                  <button
                    key={sk.id}
                    type="button"
                    onClick={() => toggleSkill(sk.name)}
                    className={`px-2.5 py-1 rounded-lg text-xs font-medium transition ${
                      isSelected
                        ? 'bg-brand-teal text-white font-semibold shadow-xs'
                        : 'bg-white dark:bg-navy-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700'
                    }`}
                  >
                    {isSelected ? `✓ ${sk.name}` : sk.name}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="flex flex-wrap gap-3 pt-1">
            <button
              type="button"
              onClick={handleManualMatch}
              disabled={loadingCV}
              className="flex-1 py-2.5 px-4 rounded-xl text-xs font-bold border border-brand-purple text-brand-purple dark:text-indigo-300 hover:bg-brand-purple hover:text-white transition"
            >
              Seçili Becerilerle Boşluk Analizi Yap
            </button>
            <button
              type="button"
              onClick={handleGenerateRoadmap}
              disabled={loadingRoadmap}
              className="flex-1 py-2.5 px-4 rounded-xl text-xs font-bold bg-gradient-to-r from-brand-teal to-emerald-600 text-white hover:opacity-95 transition shadow-md"
            >
              {loadingRoadmap ? 'Yol Haritası Hesaplanıyor...' : 'Kişiselleştirilmiş Kariyer Yol Haritası Oluştur'}
            </button>
          </div>
        </div>
      </div>

      {/* CV & Skill Gap Analysis Results */}
      {loadingCV && <LoadingSpinner label="Becerileriniz iş ilanlarıyla karşılaştırılıyor..." />}

      {analysisResult && (
        <div className="rounded-2xl bg-white dark:bg-navy-900 p-6 border border-slate-200/80 dark:border-slate-800/80 shadow-xs space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-200/70 dark:border-slate-800 pb-4">
            <div>
              <div className="flex items-center gap-2">
                <Award className="h-5 w-5 text-brand-purple" />
                <h3 className="text-lg font-extrabold text-slate-900 dark:text-white">
                  {analysisResult.target_role} — Beceri Uyum ve Boşluk Raporu
                </h3>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Kaynak: <strong>{analysisResult.filename}</strong> • İncelenen İlan Sayısı:{' '}
                <strong>{analysisResult.role_jobs_analyzed}</strong>
              </p>
            </div>

            <div className="flex items-center gap-4">
              <div className="text-right">
                <div className="text-2xl font-extrabold text-brand-teal">
                  %{analysisResult.skill_alignment_percentage}
                </div>
                <div className="text-[11px] text-slate-500 dark:text-slate-400">Beceri Örtüşme Oranı</div>
              </div>
              {analysisResult.analysis_id && (
                <button
                  onClick={handleDeleteAnalysis}
                  className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold bg-rose-500/10 text-rose-500 hover:bg-rose-500 hover:text-white transition"
                  title="CV Analiz Kaydını Sil"
                >
                  <Trash2 className="h-4 w-4" />
                  <span>CV Kaydımı Sil</span>
                </button>
              )}
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-xs text-amber-800 dark:text-amber-200">
            <strong>Önemli Metodolojik Not:</strong> {analysisResult.alignment_disclaimer}
          </div>

          {/* Education & Experience parsed from CV */}
          {analysisResult.filename.toLowerCase().endsWith('.pdf') && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200/70 dark:border-slate-800 space-y-2">
                <div className="flex items-center gap-2 text-xs font-bold text-slate-800 dark:text-slate-200">
                  <GraduationCap className="h-4 w-4 text-brand-purple" />
                  <span>Tespit Edilen Eğitim Bilgileri</span>
                </div>
                <ul className="text-xs text-slate-600 dark:text-slate-300 space-y-1 list-disc list-inside">
                  {analysisResult.education_entries.map((ed, i) => (
                    <li key={i}>{ed}</li>
                  ))}
                </ul>
              </div>
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200/70 dark:border-slate-800 space-y-2">
                <div className="flex items-center gap-2 text-xs font-bold text-slate-800 dark:text-slate-200">
                  <Clock className="h-4 w-4 text-brand-teal" />
                  <span>
                    Deneyim Analizi (Tahmini: {analysisResult.estimated_years_exp} Yıl)
                  </span>
                </div>
                <ul className="text-xs text-slate-600 dark:text-slate-300 space-y-1 list-disc list-inside">
                  {analysisResult.experience_entries.slice(0, 4).map((ex, i) => (
                    <li key={i}>{ex}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          {/* Matched vs Missing Skills */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="space-y-3">
              <h4 className="text-sm font-bold text-emerald-600 dark:text-emerald-400 flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4" />
                <span>Eşleşen Becerileriniz ({analysisResult.matched_skills.length})</span>
              </h4>
              <div className="flex flex-wrap gap-2">
                {analysisResult.matched_skills.length === 0 ? (
                  <p className="text-xs text-slate-500">Hedef pozisyonun temel becerileriyle eşleşme bulunamadı.</p>
                ) : (
                  analysisResult.matched_skills.map((m) => (
                    <div
                      key={m.name}
                      className="px-3 py-1.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-xs font-semibold text-emerald-700 dark:text-emerald-300"
                    >
                      ✓ {m.name} <span className="opacity-75">(İlanlarda %{m.demand_percentage})</span>
                    </div>
                  ))
                )}
              </div>

              <h4 className="text-sm font-bold text-slate-800 dark:text-slate-200 pt-3">
                Kategori Bazlı Mevcut Yetkinlik Sınıfınız
              </h4>
              <div className="space-y-2">
                {Object.entries(analysisResult.classified_skills).map(([cat, skList]) => (
                  <div key={cat} className="text-xs">
                    <span className="font-semibold text-brand-purple dark:text-indigo-300">{cat}: </span>
                    <span className="text-slate-700 dark:text-slate-300">{skList.join(', ')}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Missing Skills & Learning Priorities */}
            <div className="space-y-3">
              <h4 className="text-sm font-bold text-amber-600 dark:text-amber-400 flex items-center gap-2">
                <Sparkles className="h-4 w-4" />
                <span>Eksik Yetkinlikler ve Öğrenme Önceliği ({analysisResult.learning_priorities.length})</span>
              </h4>
              <div className="space-y-2.5 max-h-80 overflow-y-auto pr-1">
                {analysisResult.learning_priorities.map((lp) => (
                  <div
                    key={lp.skill_name}
                    className="p-3 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200/80 dark:border-slate-800 space-y-1"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-900 dark:text-white">
                        {lp.rank}. {lp.skill_name}{' '}
                        <span className="text-[11px] font-normal text-slate-500">({lp.category})</span>
                      </span>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-brand-purple/15 text-brand-purple dark:text-indigo-300">
                        {lp.priority} • %{lp.demand_percentage} Talep
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-600 dark:text-slate-400">{lp.reason}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Matching Job Postings */}
          <div className="space-y-3 pt-2 border-t border-slate-200/70 dark:border-slate-800">
            <h4 className="text-sm font-bold text-slate-900 dark:text-white">
              Becerilerinizle En Çok Örtüşen İş İlanları
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {analysisResult.matching_jobs.slice(0, 6).map((j) => (
                <div
                  key={j.id}
                  className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-navy-950/50 space-y-1.5"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-bold text-slate-900 dark:text-white truncate">{j.job_title}</span>
                    <span className="text-xs font-extrabold text-brand-teal shrink-0">
                      %{j.skill_alignment_score} Uyum
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-500 dark:text-slate-400">
                    {j.company_name} • {j.location} ({j.remote_type})
                  </div>
                  <div className="text-[11px]">
                    <span className="text-emerald-600 dark:text-emerald-400 font-medium">
                      Eşleşen: {j.matched_skills.join(', ') || 'Yok'}
                    </span>
                    {j.missing_skills.length > 0 && (
                      <span className="text-amber-600 dark:text-amber-400 ml-2">
                        • Eksik: {j.missing_skills.slice(0, 4).join(', ')}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Personalized Career Roadmap */}
      {loadingRoadmap && <LoadingSpinner label="Kişiselleştirilmiş kariyer yol haritanız oluşturuluyor..." />}

      {roadmap && (
        <div className="rounded-2xl bg-white dark:bg-navy-900 p-6 border border-slate-200/80 dark:border-slate-800/80 shadow-xs space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200/70 dark:border-slate-800 pb-4">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-brand-teal/15 text-brand-teal">
                <Map className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-lg font-extrabold text-slate-900 dark:text-white">
                  {roadmap.target_role} — Aşamalı Kariyer Gelişim Yol Haritası
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">{roadmap.summary}</p>
              </div>
            </div>
            <div className="px-4 py-2 rounded-xl bg-brand-purple/15 text-brand-purple dark:text-indigo-300 text-xs font-bold">
              Toplam Tahmini Süre: {roadmap.total_estimated_weeks} Hafta ({roadmap.weekly_hours} Saat/Hafta)
            </div>
          </div>

          <div className="space-y-4">
            {roadmap.steps.map((step) => (
              <div
                key={step.step_order}
                className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-slate-50/60 dark:bg-navy-950/60 space-y-3"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2.5">
                    <span className="h-7 w-7 rounded-lg bg-gradient-to-br from-brand-purple to-brand-teal text-white font-bold text-xs flex items-center justify-center">
                      {step.step_order}
                    </span>
                    <h4 className="text-sm font-bold text-slate-900 dark:text-white">{step.title}</h4>
                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-200 dark:bg-navy-800 text-slate-700 dark:text-slate-300">
                      {step.category}
                    </span>
                  </div>
                  <div className="text-xs font-semibold text-brand-teal">
                    ~{step.estimated_hours} Saat ({step.estimated_weeks} Hafta) • İlanlarda %{step.demand_percentage}
                  </div>
                </div>

                <p className="text-xs text-slate-600 dark:text-slate-300">{step.description}</p>

                <div className="p-3 rounded-xl bg-indigo-500/5 border border-indigo-500/20 text-xs text-slate-700 dark:text-slate-200">
                  <strong>Uygulamalı Kilometre Taşı Projesi:</strong> {step.milestone_project}
                </div>

                {step.free_resources.length > 0 && (
                  <div className="flex flex-wrap items-center gap-2 pt-1">
                    <span className="text-[11px] font-semibold text-slate-500 flex items-center gap-1">
                      <BookOpen className="h-3.5 w-3.5 text-brand-teal" /> Ücretsiz Kaynaklar:
                    </span>
                    {step.free_resources.map((res, idx) => (
                      <a
                        key={idx}
                        href={res.url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-medium bg-white dark:bg-navy-800 border border-slate-200 dark:border-slate-700 hover:border-brand-teal text-brand-purple dark:text-brand-teal transition"
                      >
                        <span>{res.title}</span>
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
