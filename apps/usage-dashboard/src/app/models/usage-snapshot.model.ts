export interface ModelTokenTotals {
  input_tokens?: number;
  output_tokens?: number;
  cache_read_input_tokens?: number;
  cache_creation_input_tokens?: number;
  cost_usd?: number;
}

export type ModelUsageTotals = Record<string, ModelTokenTotals>;

export interface DailyModelTokens {
  date: string;
  tokens_by_model: Record<string, number>;
}

export interface OtelMetrics {
  token_usage_by_type?: Record<string, number>;
  total_cost_usd?: number;
  has_data?: boolean;
}

export interface UsageSnapshot {
  account_label?: string;
  machine_label?: string;
  schema_version?: number;
  model_usage_totals?: ModelUsageTotals;
  daily_model_tokens?: DailyModelTokens[];
  otel_metrics?: OtelMetrics;
  stats_first_session_date?: string | null;
  stats_last_computed_date?: string | null;
}
