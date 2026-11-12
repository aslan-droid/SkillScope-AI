import React, { useEffect, useState } from 'react';
import { Bot, Cpu, Database, HelpCircle, Send, ShieldAlert, Sparkles, User } from 'lucide-react';
import { api } from '../services/api';
import type { AssistantEvidence } from '../types';
import { ErrorBanner } from '../components/StatusUI';

interface ChatTurn {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  engineUsed?: string;
  isFallback?: boolean;
  evidence?: AssistantEvidence;
  timestamp: string;
}

export const AssistantPage: React.FC = () => {
  const [statusInfo, setStatusInfo] = useState<{
    ollamaAvailable: boolean;
    baseUrl: string;
    modelName: string;
    suggestedQuestions: string[];
  }>({
    ollamaAvailable: false,
    baseUrl: 'http://localhost:11434',
    modelName: 'gemma3:1b',
    suggestedQuestions: [
      'Veri analisti olmak için neler öğrenmeliyim?',
      'Python mı R mı daha fazla aranıyor?',
      "Gaziantep'te hangi teknoloji alanlarında ilan var?",
      'SQL ile birlikte en çok hangi beceriler aranıyor?',
      "CV'm hangi pozisyonlarla daha çok eşleşiyor?",
    ],
  });

  const [sessionId, setSessionId] = useState<number | null>(null);
  const [questionInput, setQuestionInput] = useState('');
  const [messages, setMessages] = useState<ChatTurn[]>([]);
  const [activeEvidence, setActiveEvidence] = useState<AssistantEvidence | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getAssistantStatus()
      .then((res) => {
        setStatusInfo({
          ollamaAvailable: res.ollama.available,
          baseUrl: res.ollama.base_url,
          modelName: res.ollama.configured_model,
          suggestedQuestions: res.suggested_questions,
        });
      })
      .catch(() => {});
  }, []);

  const submitQuestion = async (qText: string) => {
    const trimmed = qText.trim();
    if (!trimmed || loading) return;

    const userTurn: ChatTurn = {
      id: Date.now(),
      role: 'user',
      content: trimmed,
      timestamp: new Date().toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userTurn]);
    setQuestionInput('');
    setLoading(true);
    setError(null);

    try {
      const res = await api.askAssistant(trimmed, sessionId);
      setSessionId(res.session_id);
      const botTurn: ChatTurn = {
        id: res.message_id,
        role: 'assistant',
        content: res.answer,
        engineUsed: res.engine_used,
        isFallback: res.is_fallback,
        evidence: res.evidence,
        timestamp: new Date().toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, botTurn]);
      setActiveEvidence(res.evidence);
    } catch (err: any) {
      setError(err.message || 'AI asistanı yanıt üretirken hata oluştu.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Engine Status Banner */}
      <div className="rounded-2xl bg-white dark:bg-navy-900 p-4 border border-slate-200/80 dark:border-slate-800/80 shadow-xs flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-brand-purple/15 text-brand-purple">
            <Bot className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-900 dark:text-white">
              Katmanlı Kariyer ve Piyasa Zekâ Asistanı
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              İzin verilen veritabanı analiz fonksiyonlarıyla uydurma istatistik üretmeden yanıt verir
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span
            className={`px-3 py-1 rounded-full font-semibold flex items-center gap-1.5 ${
              statusInfo.ollamaAvailable
                ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-300'
                : 'bg-amber-500/15 text-amber-600 dark:text-amber-300'
            }`}
          >
            <Cpu className="h-3.5 w-3.5" />
            {statusInfo.ollamaAvailable
              ? `Yerel Ollama Aktif (${statusInfo.modelName})`
              : 'Ollama Kapalı • Kural & İstatistik Fallback Motoru Aktif'}
          </span>
        </div>
      </div>

      {error && <ErrorBanner message={error} onRetry={() => setError(null)} />}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Chat Column */}
        <div className="lg:col-span-8 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800/80 shadow-xs flex flex-col h-[620px]">
          {/* Suggested Quick Prompts */}
          <div className="p-4 border-b border-slate-200/70 dark:border-slate-800 bg-slate-50/50 dark:bg-navy-950/50">
            <div className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 mb-2 flex items-center gap-1.5">
              <Sparkles className="h-3.5 w-3.5 text-brand-teal" />
              <span>Örnek Veri Odaklı Sorular (Tıklayarak Sorun):</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {statusInfo.suggestedQuestions.map((sq) => (
                <button
                  key={sq}
                  onClick={() => submitQuestion(sq)}
                  disabled={loading}
                  className="px-2.5 py-1 rounded-lg text-xs font-medium bg-white dark:bg-navy-800 border border-slate-200 dark:border-slate-700 hover:border-brand-purple text-slate-700 dark:text-slate-200 transition"
                >
                  {sq}
                </button>
              ))}
            </div>
          </div>

          {/* Messages List */}
          <div className="flex-1 p-5 overflow-y-auto space-y-4">
            {messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center px-6">
                <div className="h-12 w-12 rounded-2xl bg-gradient-to-br from-brand-purple/20 to-brand-teal/20 flex items-center justify-center text-brand-teal mb-3">
                  <HelpCircle className="h-6 w-6" />
                </div>
                <h3 className="text-base font-bold text-slate-800 dark:text-slate-100">
                  Verilere Dayalı Kariyer Asistanına Hoş Geldiniz
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 max-w-md mt-1 leading-relaxed">
                  Yukarıdaki örnek sorulardan birini seçebilir veya Türkiye'deki şehirler, pozisyonlar, beceri
                  karşılaştırmaları ve CV eşleşmeniz hakkında kendi sorunuzu yazabilirsiniz.
                </p>
              </div>
            ) : (
              messages.map((m) => (
                <div
                  key={m.id}
                  onClick={() => m.evidence && setActiveEvidence(m.evidence)}
                  className={`flex gap-3 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  {m.role === 'assistant' && (
                    <div className="h-8 w-8 rounded-xl bg-gradient-to-br from-brand-purple to-brand-teal text-white flex items-center justify-center shrink-0 mt-1">
                      <Bot className="h-4 w-4" />
                    </div>
                  )}
                  <div
                    className={`max-w-[85%] rounded-2xl p-4 text-xs leading-relaxed space-y-2 ${
                      m.role === 'user'
                        ? 'bg-brand-purple text-white'
                        : 'bg-slate-100 dark:bg-navy-950 border border-slate-200/80 dark:border-slate-800 text-slate-800 dark:text-slate-100 cursor-pointer hover:border-brand-teal/50'
                    }`}
                  >
                    {m.role === 'assistant' && (
                      <div className="flex flex-wrap items-center justify-between gap-2 pb-1.5 border-b border-slate-200 dark:border-slate-800 text-[10px]">
                        <span className="font-bold text-brand-teal uppercase tracking-wider">
                          {m.isFallback
                            ? 'Kural & İstatistik Tabanlı Analitik Yanıt (Fallback)'
                            : `Yerel LLM Yanıtı (${m.engineUsed})`}
                        </span>
                        <span className="text-slate-400">{m.timestamp}</span>
                      </div>
                    )}
                    <div className="whitespace-pre-line">{m.content}</div>
                  </div>
                  {m.role === 'user' && (
                    <div className="h-8 w-8 rounded-xl bg-slate-200 dark:bg-navy-800 text-slate-700 dark:text-slate-200 flex items-center justify-center shrink-0 mt-1">
                      <User className="h-4 w-4" />
                    </div>
                  )}
                </div>
              ))
            )}
            {loading && (
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <div className="h-2 w-2 rounded-full bg-brand-teal animate-ping" />
                <span>Veritabanı istatistikleri sorgulanıyor ve yanıt hazırlanıyor...</span>
              </div>
            )}
          </div>

          {/* Input Form */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              submitQuestion(questionInput);
            }}
            className="p-4 border-t border-slate-200/70 dark:border-slate-800 flex items-center gap-2"
          >
            <input
              type="text"
              value={questionInput}
              onChange={(e) => setQuestionInput(e.target.value)}
              placeholder="Örn: Türkiye'de veri analisti olmak için en çok hangi teknolojiler aranıyor?"
              className="flex-1 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-navy-950 px-4 py-2.5 text-xs focus:outline-none focus:border-brand-purple"
            />
            <button
              type="submit"
              disabled={loading || !questionInput.trim()}
              className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-brand-purple to-brand-teal text-white text-xs font-bold flex items-center gap-1.5 hover:opacity-95 disabled:opacity-50 transition"
            >
              <span>Gönder</span>
              <Send className="h-3.5 w-3.5" />
            </button>
          </form>
        </div>

        {/* Right Column: Evidence & Data Scope Panel */}
        <div className="lg:col-span-4 rounded-2xl bg-white dark:bg-navy-900 p-6 border border-slate-200/80 dark:border-slate-800/80 shadow-xs space-y-4">
          <div className="flex items-center gap-2 text-sm font-bold text-slate-900 dark:text-white border-b border-slate-200/70 dark:border-slate-800 pb-3">
            <Database className="h-4 w-4 text-brand-teal" />
            <span>Yanıt Kanıtı ve Veri Kapsamı</span>
          </div>

          {!activeEvidence ? (
            <div className="text-xs text-slate-500 dark:text-slate-400 space-y-2 py-8 text-center">
              <p>Bir soru sorduğunuzda yanıtın dayandığı:</p>
              <ul className="space-y-1 font-medium text-slate-700 dark:text-slate-300">
                <li>• Veri Dönemi</li>
                <li>• Örneklem Büyüklüğü (İlan Sayısı)</li>
                <li>• Kullanılan Analiz Yöntemi</li>
                <li>• Veri Kaynağı</li>
                <li>• Güvenilirlik Sınırlılıkları</li>
              </ul>
              <p>burada şeffaf biçimde gösterilir.</p>
            </div>
          ) : (
            <div className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200/70 dark:border-slate-800">
                  <span className="text-[10px] text-slate-500 block">Örneklem Büyüklüğü</span>
                  <span className="text-base font-extrabold text-brand-teal">
                    {activeEvidence.sample_size} İlan
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200/70 dark:border-slate-800">
                  <span className="text-[10px] text-slate-500 block">Veri Dönemi</span>
                  <span className="text-xs font-bold text-slate-800 dark:text-slate-200">
                    {activeEvidence.data_period}
                  </span>
                </div>
              </div>

              <div className="space-y-1">
                <span className="text-[11px] font-semibold text-slate-500">Kullanılan Analiz Fonksiyonu:</span>
                <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200/70 dark:border-slate-800 font-semibold text-brand-purple dark:text-indigo-300">
                  {activeEvidence.analysis_method}
                </div>
              </div>

              <div className="space-y-1">
                <span className="text-[11px] font-semibold text-slate-500">Veri Kaynağı:</span>
                <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200/70 dark:border-slate-800 text-slate-700 dark:text-slate-300">
                  {activeEvidence.source}
                </div>
              </div>

              {activeEvidence.highlights && activeEvidence.highlights.length > 0 && (
                <div className="space-y-1.5">
                  <span className="text-[11px] font-semibold text-slate-500">Öne Çıkan Metrikler:</span>
                  <div className="space-y-1.5">
                    {activeEvidence.highlights.map((h, i) => (
                      <div
                        key={i}
                        className="flex items-center justify-between px-3 py-2 rounded-lg bg-brand-teal/10 text-slate-800 dark:text-slate-200"
                      >
                        <span>{h.label}</span>
                        <strong className="text-brand-teal">{h.value}</strong>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-800 dark:text-amber-200 space-y-1">
                <div className="font-bold flex items-center gap-1.5">
                  <ShieldAlert className="h-4 w-4 shrink-0" />
                  <span>Güvenilirlik Sınırlılıkları</span>
                </div>
                <p className="text-[11px] leading-relaxed">{activeEvidence.limitations}</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
