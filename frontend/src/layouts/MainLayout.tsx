import React, { useEffect, useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  Activity,
  BarChart3,
  Bot,
  Briefcase,
  Compass,
  Cpu,
  Database,
  Info,
  LayoutDashboard,
  Menu,
  Moon,
  Sparkles,
  Sun,
  X,
} from 'lucide-react';
import { useTheme } from '../hooks/useTheme';
import { api } from '../services/api';

interface NavItem {
  to: string;
  label: string;
  subtitle: string;
  group: 'Piyasa & Keşif' | 'Kariyer & AI' | 'Veri & Modeller';
  icon: React.ComponentType<{ className?: string }>;
}

const NAV_ITEMS: NavItem[] = [
  {
    to: '/',
    label: 'Genel Bakış',
    subtitle: 'Canlı İş Piyasası Dashboard',
    group: 'Piyasa & Keşif',
    icon: LayoutDashboard,
  },
  {
    to: '/market',
    label: 'İş Piyasası Analizi',
    subtitle: 'Şehir, Pozisyon, Sektör & Maaş',
    group: 'Piyasa & Keşif',
    icon: BarChart3,
  },
  {
    to: '/skills',
    label: 'Beceri Keşfetme',
    subtitle: 'Birliktelik & Talep Trendleri',
    group: 'Piyasa & Keşif',
    icon: Compass,
  },
  {
    to: '/career',
    label: 'Kariyer Eşleştirme',
    subtitle: 'CV Analizi & Yol Haritası',
    group: 'Kariyer & AI',
    icon: Briefcase,
  },
  {
    to: '/assistant',
    label: 'AI Kariyer Asistanı',
    subtitle: 'Veriye Dayalı Akıllı Yanıtlar',
    group: 'Kariyer & AI',
    icon: Bot,
  },
  {
    to: '/datasets',
    label: 'Veri Yönetimi',
    subtitle: 'Canlı API & CSV İçe Aktarma',
    group: 'Veri & Modeller',
    icon: Database,
  },
  {
    to: '/models',
    label: 'Model Performansı',
    subtitle: 'MAE, RMSE, F1 & Tahminleme',
    group: 'Veri & Modeller',
    icon: Cpu,
  },
  {
    to: '/about',
    label: 'Hakkında',
    subtitle: 'Mimari, Veri & Sınırlılıklar',
    group: 'Veri & Modeller',
    icon: Info,
  },
];

const NAV_GROUPS: Array<NavItem['group']> = ['Piyasa & Keşif', 'Kariyer & AI', 'Veri & Modeller'];

export const MainLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [liveJobsCount, setLiveJobsCount] = useState<number | null>(null);
  const { theme, toggleTheme } = useTheme();
  const location = useLocation();

  useEffect(() => {
    let mounted = true;
    api
      .getSyncStatus()
      .then((res) => {
        if (mounted) setLiveJobsCount(res.real_jobs_count);
      })
      .catch(() => {
        /* Başlangıçta erişilemezse sessiz geç */
      });
    return () => {
      mounted = false;
    };
  }, [location.pathname]);

  const currentNav = NAV_ITEMS.find((item) =>
    item.to === '/' ? location.pathname === '/' : location.pathname.startsWith(item.to)
  ) || NAV_ITEMS[0];

  return (
    <div className="min-h-screen flex bg-slate-50 dark:bg-navy-950 text-slate-900 dark:text-slate-100">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-[60] focus:px-4 focus:py-2 focus:rounded-xl focus:bg-brand-purple focus:text-white focus:text-xs focus:font-semibold"
      >
        Ana içeriğe geç
      </a>
      {/* Mobile Backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-xs lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Left Sidebar */}
      <aside
        className={`fixed lg:static inset-y-0 left-0 z-50 w-72 shrink-0 flex flex-col bg-navy-900 text-slate-100 border-r border-slate-800/80 transition-transform duration-200 ease-in-out ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        {/* Brand Header */}
        <div className="h-18 px-6 py-5 flex items-center justify-between border-b border-slate-800/80">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-brand-purple to-brand-teal flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Sparkles className="h-5 w-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-base tracking-tight text-white">SkillScope</span>
                <span className="text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-brand-teal/20 text-brand-teal border border-brand-teal/30">
                  AI
                </span>
              </div>
              <p className="text-[11px] text-slate-400">Kariyer & Piyasa Zekâsı</p>
            </div>
          </div>
          <button
            onClick={() => setMobileOpen(false)}
            className="lg:hidden p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
            aria-label="Menüyü kapat"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Navigation Links (Hick & Gestalt Gruplandırma) */}
        <nav aria-label="Ana navigasyon" className="flex-1 px-3 py-4 space-y-5 overflow-y-auto">
          {NAV_GROUPS.map((groupName) => (
            <div key={groupName} className="space-y-1">
              <div className="px-3 pb-1 text-[10px] font-bold uppercase tracking-wider text-slate-400/90">
                {groupName}
              </div>
              {NAV_ITEMS.filter((item) => item.group === groupName).map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end={item.to === '/'}
                    onClick={() => setMobileOpen(false)}
                    className={({ isActive }) =>
                      `group flex items-center gap-3.5 px-3.5 min-h-[44px] py-2 rounded-xl text-sm transition-all ${
                        isActive
                          ? 'bg-gradient-to-r from-brand-purple/95 to-indigo-600/85 text-white font-semibold shadow-md shadow-indigo-950/50 border-l-2 border-brand-teal'
                          : 'text-slate-300 hover:bg-navy-800/90 hover:text-white'
                      }`
                    }
                  >
                    <Icon className="h-4 w-4 shrink-0 text-brand-teal group-hover:scale-110 transition-transform" />
                    <div className="truncate">
                      <div className="leading-tight">{item.label}</div>
                      <div className="text-[11px] text-slate-400 group-hover:text-slate-200 truncate">
                        {item.subtitle}
                      </div>
                    </div>
                  </NavLink>
                );
              })}
            </div>
          ))}
        </nav>

        {/* Zero-Budget & Privacy Badge */}
        <div className="p-4 m-3 rounded-xl bg-navy-800/80 border border-slate-700/60 text-xs space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="font-semibold text-brand-teal">Sıfır Bütçe Mimarisi</span>
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
          </div>
          <p className="text-[11px] text-slate-300 leading-relaxed">
            Ücretli bulut/LLM API bağımlılığı yoktur. PostgreSQL, Scikit-learn ve Yerel AI/Fallback ile çalışır.
          </p>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Header */}
        <header className="sticky top-0 z-30 h-16 px-4 sm:px-8 bg-white/85 dark:bg-navy-900/85 backdrop-blur-md border-b border-slate-200/80 dark:border-slate-800/80 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 min-w-0">
            <button
              onClick={() => setMobileOpen(true)}
              className="lg:hidden p-2 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-navy-800"
              aria-label="Menüyü aç"
            >
              <Menu className="h-5 w-5" />
            </button>
            <div className="truncate">
              <h1 className="text-base sm:text-lg font-bold tracking-tight text-slate-900 dark:text-white truncate">
                {currentNav.label}
              </h1>
              <p className="text-xs text-slate-500 dark:text-slate-400 hidden sm:block truncate">
                {currentNav.subtitle}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {liveJobsCount !== null && (
              <div
                className="hidden sm:inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-emerald-500/10 border border-emerald-500/25 text-emerald-700 dark:text-emerald-300 text-xs font-medium tabular-nums"
                title="Veritabanındaki doğrulanmış gerçek iş ilanı sayısı"
              >
                <Activity className="h-3.5 w-3.5 text-emerald-500" />
                <span>{liveJobsCount} Canlı İlan</span>
              </div>
            )}

            <button
              onClick={toggleTheme}
              className="inline-flex items-center gap-2 px-3 min-h-[40px] rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-100/80 dark:bg-navy-800 text-xs font-medium text-slate-700 dark:text-slate-200 hover:border-brand-purple transition"
              title="Temayı Değiştir"
              aria-label="Aydınlık veya koyu temayı değiştir"
            >
              {theme === 'dark' ? (
                <>
                  <Sun className="h-4 w-4 text-amber-400" />
                  <span className="hidden sm:inline">Aydınlık Tema</span>
                </>
              ) : (
                <>
                  <Moon className="h-4 w-4 text-brand-purple" />
                  <span className="hidden sm:inline">Koyu Tema</span>
                </>
              )}
            </button>

            <div className="hidden md:flex items-center gap-2.5 pl-3 border-l border-slate-200 dark:border-slate-800">
              <div className="h-8 w-8 rounded-full bg-gradient-to-tr from-brand-purple to-brand-teal text-white font-bold text-xs flex items-center justify-center">
                KA
              </div>
              <div className="text-xs">
                <div className="font-semibold text-slate-800 dark:text-slate-100">Kariyer Analisti</div>
                <div className="text-[11px] text-emerald-600 dark:text-emerald-400">Yerel Oturum Aktif</div>
              </div>
            </div>
          </div>
        </header>

        {/* Page Body */}
        <main id="main-content" className="flex-1 p-4 sm:p-6 lg:p-8 max-w-[1440px] w-full mx-auto space-y-6">
          {children}
        </main>
      </div>
    </div>
  );
};
