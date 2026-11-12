import React from 'react';
import { AlertCircle, CheckCircle2, Database, Info, Loader2 } from 'lucide-react';

export const LoadingSpinner: React.FC<{ label?: string }> = ({ label = 'Veriler analiz ediliyor...' }) => (
  <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
    <Loader2 className="h-9 w-9 animate-spin text-brand-purple mb-3" />
    <p className="text-sm font-medium text-slate-600 dark:text-slate-300">{label}</p>
  </div>
);

export const ErrorBanner: React.FC<{ message: string; onRetry?: () => void }> = ({ message, onRetry }) => (
  <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-rose-700 dark:text-rose-300 flex items-start justify-between gap-4">
    <div className="flex items-start gap-3">
      <AlertCircle className="h-5 w-5 shrink-0 mt-0.5 text-rose-500" />
      <div className="text-sm">
        <p className="font-semibold">İşlem Sırasında Hata Oluştu</p>
        <p className="mt-0.5 opacity-90">{message}</p>
      </div>
    </div>
    {onRetry && (
      <button
        onClick={onRetry}
        className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-rose-500 text-white hover:bg-rose-600 transition"
      >
        Tekrar Dene
      </button>
    )}
  </div>
);

export const SuccessBanner: React.FC<{ message: string; onClose?: () => void }> = ({ message, onClose }) => (
  <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4 text-emerald-800 dark:text-emerald-200 flex items-center justify-between gap-4">
    <div className="flex items-center gap-3">
      <CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-500" />
      <p className="text-sm font-medium">{message}</p>
    </div>
    {onClose && (
      <button onClick={onClose} className="text-xs underline opacity-75 hover:opacity-100">
        Kapat
      </button>
    )}
  </div>
);

export const EmptyState: React.FC<{
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
}> = ({ title, description, actionLabel, onAction }) => (
  <div className="rounded-2xl border border-dashed border-slate-300 dark:border-slate-700/80 bg-white/50 dark:bg-navy-900/40 p-10 text-center">
    <Database className="h-10 w-10 mx-auto text-brand-teal mb-3 opacity-80" />
    <h3 className="text-base font-semibold text-slate-800 dark:text-slate-100">{title}</h3>
    <p className="text-sm text-slate-500 dark:text-slate-400 max-w-md mx-auto mt-1">{description}</p>
    {actionLabel && onAction && (
      <button
        onClick={onAction}
        className="mt-4 inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold bg-brand-purple text-white hover:bg-indigo-500 transition shadow-sm"
      >
        {actionLabel}
      </button>
    )}
  </div>
);

export const SyntheticDataBanner: React.FC<{ demoCount: number; realCount: number }> = ({
  demoCount,
  realCount,
}) => {
  if (demoCount <= 0) return null;
  return (
    <div className="rounded-xl border border-cyan-500/30 bg-cyan-500/10 px-4 py-3 text-xs text-cyan-900 dark:text-cyan-200 flex flex-wrap items-center justify-between gap-2">
      <div className="flex items-center gap-2.5">
        <Info className="h-4 w-4 shrink-0 text-brand-teal" />
        <span>
          <strong>Şeffaf Veri Etiketi:</strong> Mevcut analizlerde{' '}
          <span className="font-semibold underline">{demoCount} adet Sentetik Demo İlanı (SYNTHETIC_DEMO)</span>{' '}
          {realCount > 0 ? `ve ${realCount} adet kullanıcı/gerçek ilanı` : ''} bulunmaktadır. Demo veriler sistem
          yeteneklerini göstermek içindir; <strong>Veri Yönetimi</strong> sayfasından gerçek CSV yükleyebilir veya
          demo veriyi silebilirsiniz.
        </span>
      </div>
    </div>
  );
};
