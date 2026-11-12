import type {
  AssistantAskResponse,
  CareerRoadmapResponse,
  CVAnalysisResult,
  DashboardSummary,
  DatasetItem,
  MarketAnalytics,
  ModelVersionItem,
  SkillCatalogItem,
  SkillDeepDive,
  SkillForecastResponse,
} from '../types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...(options?.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
      ...(options?.headers || {}),
    },
  });

  if (!response.ok) {
    let errorMessage = `Sunucu hatası (${response.status})`;
    try {
      const errJson = await response.json();
      if (errJson.detail) {
        errorMessage = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch {
      // ignore json parse error
    }
    throw new Error(errorMessage);
  }

  return response.json() as Promise<T>;
}

export const api = {
  getHealth: () =>
    request<{
      status: string;
      project: string;
      environment: string;
      database_connected: boolean;
      jobs_count: number;
      skills_count: number;
    }>('/health'),

  getDashboardSummary: (includeDemo = true) =>
    request<DashboardSummary>(`/analytics/dashboard?include_demo=${includeDemo}`),

  getMarketAnalytics: (params: {
    city?: string;
    role?: string;
    sector?: string;
    remote_type?: string;
    skill?: string;
    date_from?: string;
    date_to?: string;
    include_demo?: boolean;
  }) => {
    const search = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== '' && v !== 'Tümü') {
        search.set(k, String(v));
      }
    });
    return request<MarketAnalytics>(`/analytics/market?${search.toString()}`);
  },

  listSkills: (category?: string, includeDemo = true) => {
    const search = new URLSearchParams({ include_demo: String(includeDemo) });
    if (category && category !== 'Tümü') search.set('category', category);
    return request<{ total_skills: number; total_jobs: number; items: SkillCatalogItem[] }>(
      `/skills?${search.toString()}`
    );
  },

  getSkillDeepDive: (skillIdentifier: string, includeDemo = true) =>
    request<SkillDeepDive>(`/skills/${encodeURIComponent(skillIdentifier)}?include_demo=${includeDemo}`),

  analyzeCV: (file: File, targetRole: string) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('target_role', targetRole);
    formData.append('save_record', 'true');
    return request<CVAnalysisResult>('/cv/analyze', {
      method: 'POST',
      body: formData,
    });
  },

  deleteCVAnalysis: (analysisId: number) =>
    request<{ status: string; analysis_id: number; message: string }>(`/cv/${analysisId}`, {
      method: 'DELETE',
    }),

  matchCareerSkills: (payload: {
    target_role: string;
    current_skills: string[];
    current_level: string;
  }) =>
    request<CVAnalysisResult>('/career/match', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  generateRoadmap: (payload: {
    target_role: string;
    current_level: string;
    current_skills: string[];
    weekly_hours: number;
  }) =>
    request<CareerRoadmapResponse>('/career/roadmap', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getAssistantStatus: () =>
    request<{
      ollama: {
        available: boolean;
        base_url: string;
        configured_model: string;
        installed_models: string[];
      };
      fallback_engine: string;
      zero_cost_guaranteed: boolean;
      suggested_questions: string[];
    }>('/assistant/status'),

  askAssistant: (question: string, sessionId?: number | null) =>
    request<AssistantAskResponse>('/assistant/ask', {
      method: 'POST',
      body: JSON.stringify({ question, session_id: sessionId || undefined }),
    }),

  listDatasets: () => request<DatasetItem[]>('/datasets'),

  getSyncStatus: () =>
    request<{
      auto_sync_enabled: boolean;
      interval_minutes: number;
      real_jobs_count: number;
      demo_jobs_count: number;
      is_syncing: boolean;
      last_sync_at: string | null;
      next_sync_at: string | null;
      last_sync_status: string;
      last_sync_summary: any;
    }>('/datasets/sync-status'),

  syncLiveSources: (sources: string[] = ['lever_turkey', 'remotive', 'arbeitnow'], limitPerSource = 80) =>
    request<any>('/datasets/sync-live', {
      method: 'POST',
      body: JSON.stringify({
        sources,
        limit_per_source: limitPerSource,
        retrain_models: true,
      }),
    }),

  purgeDemoData: () =>
    request<{
      status: string;
      deleted_jobs: number;
      deleted_job_skills: number;
      deleted_imports: number;
      deleted_sources: number;
    }>('/datasets/demo-data', {
      method: 'DELETE',
    }),

  uploadDatasetCsv: (file: File, sourceName: string, licenseName: string, columnMappingJson?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('source_name', sourceName);
    formData.append('license_name', licenseName);
    if (columnMappingJson && columnMappingJson.trim()) {
      formData.append('column_mapping_json', columnMappingJson);
    }
    return request<any>('/datasets/upload', {
      method: 'POST',
      body: formData,
    });
  },

  loadDemoDataset: (forceReload = true) =>
    request<any>(`/datasets/load-demo?force_reload=${forceReload}`, {
      method: 'POST',
    }),

  deleteDataset: (datasetId: number) =>
    request<{ status: string; dataset_id: number; filename: string }>(`/datasets/${datasetId}`, {
      method: 'DELETE',
    }),

  listModels: () => request<ModelVersionItem[]>('/models'),

  trainModels: () =>
    request<any>('/models/train', {
      method: 'POST',
    }),

  getSkillForecast: (skillIdentifier: string, horizonMonths = 3, includeDemo = true) =>
    request<SkillForecastResponse>(
      `/models/forecast/${encodeURIComponent(skillIdentifier)}?horizon_months=${horizonMonths}&include_demo=${includeDemo}`
    ),

  classifyJobText: (payload: { job_title: string; description: string; sector?: string }) =>
    request<{
      predicted_category: string;
      confidence: number;
      probabilities: Record<string, number>;
      is_experimental: boolean;
    }>('/models/classify', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};
