export interface SkillStat {
  name: string;
  slug: string;
  category: string;
  count: number;
  percentage: number;
}

export interface RoleStat {
  role: string;
  count: number;
  percentage: number;
}

export interface SectorStat {
  sector: string;
  count: number;
  percentage: number;
}

export interface CityStat {
  city: string;
  count: number;
  percentage: number;
}

export interface RemoteStat {
  type: string;
  count: number;
  percentage: number;
}

export interface JobSummaryItem {
  id: number;
  job_title: string;
  normalized_role: string;
  company_name: string;
  location: string;
  sector: string;
  remote_type: string;
  posted_date: string;
  source_name?: string;
  source_url?: string | null;
  predicted_category?: string;
  is_demo: boolean;
  skills: string[];
}

export interface DashboardSummary {
  total_jobs: number;
  demo_jobs_count: number;
  real_jobs_count: number;
  unique_companies: number;
  unique_cities: number;
  remote_ratio: number;
  hybrid_ratio: number;
  onsite_ratio: number;
  date_range: {
    min_date: string | null;
    max_date: string | null;
  };
  top_skills: SkillStat[];
  top_roles: RoleStat[];
  sector_distribution: SectorStat[];
  city_distribution: CityStat[];
  remote_distribution: RemoteStat[];
  recent_jobs: JobSummaryItem[];
  skill_trends: Array<Record<string, string | number>>;
}

export interface MarketAnalytics {
  sample_size: number;
  date_range: {
    min_date: string | null;
    max_date: string | null;
  };
  filters_available: {
    cities: string[];
    roles: string[];
    sectors: string[];
    skills: string[];
    remote_types: string[];
  };
  top_skills: SkillStat[];
  role_distribution: RoleStat[];
  city_comparison: CityStat[];
  sector_distribution: SectorStat[];
  remote_distribution: RemoteStat[];
  salary_analytics: {
    sufficient_data: boolean;
    sample_size?: number;
    currency?: string;
    reason?: string | null;
    by_role: Array<{
      role: string;
      count: number;
      avg_min: number;
      avg_max: number;
      avg_midpoint: number;
    }>;
  };
  skill_trends: Array<Record<string, string | number>>;
}

export interface SkillCatalogItem {
  id: number;
  name: string;
  slug: string;
  category: string;
  aliases: string[];
  prerequisites: string[];
  description?: string;
  estimated_hours: number;
  learning_resources: Array<{ title: string; url: string; type: string }>;
  demand_count: number;
  demand_percentage: number;
}

export interface SkillDeepDive {
  skill: SkillCatalogItem;
  total_jobs_analyzed: number;
  demand_count: number;
  demand_percentage: number;
  co_occurring_skills: Array<{
    name: string;
    slug: string;
    category: string;
    co_count: number;
    co_percentage: number;
  }>;
  by_role: RoleStat[];
  by_sector: SectorStat[];
  by_city: CityStat[];
  monthly_trend: Array<{ period: string; count: number }>;
  sample_jobs: JobSummaryItem[];
  forecast?: SkillForecastResponse;
}

export interface SkillForecastResponse {
  forecast_available: boolean;
  skill_name: string;
  skill_slug?: string;
  reason?: string;
  data_period?: string;
  includes_demo_data?: boolean;
  disclaimer?: string;
  metrics?: {
    mae: number;
    rmse: number;
    train_months: number;
    test_months: number;
    total_observations: number;
  } | null;
  history: Array<{
    period: string;
    actual: number;
    split?: string;
    test_predicted?: number;
  }>;
  comparison?: Array<{
    period: string;
    actual: number;
    predicted: number;
    error: number;
  }>;
  forecast: Array<{
    period: string;
    predicted: number;
    lower_bound: number;
    upper_bound: number;
  }>;
}

export interface CVAnalysisResult {
  analysis_id: number | null;
  filename: string;
  target_role: string;
  role_jobs_analyzed: number;
  extracted_skills: string[];
  classified_skills: Record<string, string[]>;
  education_entries: string[];
  experience_entries: string[];
  estimated_years_exp: number;
  skill_alignment_percentage: number;
  alignment_disclaimer: string;
  matched_skills: Array<{
    name: string;
    category: string;
    demand_percentage: number;
  }>;
  missing_skills: Array<{
    name: string;
    slug: string;
    category: string;
    demand_percentage: number;
    priority: string;
    prerequisites: string[];
    estimated_hours: number;
    learning_resources: Array<{ title: string; url: string; type: string }>;
  }>;
  learning_priorities: Array<{
    rank: number;
    skill_name: string;
    category: string;
    priority: string;
    demand_percentage: number;
    estimated_hours: number;
    reason: string;
    free_resources: Array<{ title: string; url: string; type: string }>;
  }>;
  matching_jobs: Array<{
    id: number;
    job_title: string;
    normalized_role: string;
    company_name: string;
    location: string;
    sector: string;
    remote_type: string;
    posted_date: string;
    source_name?: string;
    source_url?: string | null;
    skill_alignment_score: number;
    matched_skills: string[];
    missing_skills: string[];
    is_demo: boolean;
  }>;
  privacy_notice: string;
}

export interface CareerRoadmapResponse {
  roadmap_id: number;
  target_role: string;
  current_level: string;
  weekly_hours: number;
  current_skills: string[];
  missing_skills: string[];
  total_estimated_weeks: number;
  summary: string;
  steps: Array<{
    step_order: number;
    skill_name: string;
    category: string;
    title: string;
    description: string;
    demand_percentage: number;
    estimated_hours: number;
    estimated_weeks: number;
    prerequisites: string[];
    free_resources: Array<{ title: string; url: string; type: string }>;
    milestone_project: string;
  }>;
  created_at: string;
}

export interface AssistantEvidence {
  data_period: string;
  sample_size: number;
  analysis_method: string;
  source: string;
  limitations: string;
  highlights: Array<{ label: string; value: string }>;
}

export interface AssistantAskResponse {
  session_id: number;
  message_id: number;
  question: string;
  answer: string;
  engine_used: string;
  is_fallback: boolean;
  ollama_status: {
    available: boolean;
    base_url: string;
    configured_model: string;
    installed_models: string[];
  };
  evidence: AssistantEvidence;
  created_at: string;
}

export interface DatasetItem {
  id: number;
  filename: string;
  source_name: string;
  source_type: string;
  license_name: string;
  is_demo: boolean;
  total_rows: number;
  imported_rows: number;
  duplicate_rows: number;
  invalid_rows: number;
  validation_status: string;
  validation_summary?: {
    mapped_columns?: Record<string, string>;
    missing_optional_columns?: string[];
    extracted_skill_links?: number;
    row_errors?: string[];
  };
  created_at: string;
}

export interface ModelVersionItem {
  id: number;
  model_name: string;
  model_type: string;
  version: string;
  algorithm: string;
  training_samples: number;
  test_samples: number;
  metrics: Record<string, any>;
  comparison_data: Array<Record<string, any>>;
  is_experimental: boolean;
  trained_on_demo: boolean;
  notes?: string;
  trained_at: string;
}
