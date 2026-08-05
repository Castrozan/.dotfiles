import { ModelUsageTotals } from './usage-snapshot.model';

export interface TokenTotals {
  input_tokens: number;
  output_tokens: number;
  cache_read_input_tokens: number;
  cache_creation_input_tokens: number;
  cost_usd: number;
}

export interface AggregatedOtelMetrics {
  token_usage_by_type: Record<string, number>;
  total_cost_usd: number;
  has_data: boolean;
}

export interface AccountView {
  account_label: string;
  machine_count: number;
  model_usage_totals: ModelUsageTotals;
  token_totals: TokenTotals;
  daily_total_tokens: Record<string, number>;
  otel_metrics: AggregatedOtelMetrics;
  first_session_date: string | null;
  last_computed_date: string | null;
}

export interface UsageSummary {
  account_count: number;
  machine_count: number;
  token_totals: TokenTotals;
  otel_metrics: AggregatedOtelMetrics;
  first_session_date: string | null;
  last_computed_date: string | null;
}

export interface ChartAccountSeries {
  account_label: string;
  values: (number | null)[];
}

export interface ChartSeries {
  dates: string[];
  series: ChartAccountSeries[];
}

export interface UsageViewModel {
  accounts: AccountView[];
  summary: UsageSummary;
  chart: ChartSeries;
}
