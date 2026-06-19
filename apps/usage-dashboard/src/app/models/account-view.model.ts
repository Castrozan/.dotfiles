import { MemoryRecallSavings, ModelUsageTotals, OtelMetrics } from './usage-snapshot.model';

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

export interface AggregatedMemoryRecallSavings
  extends Required<Omit<MemoryRecallSavings, 'suppressed_recall_event_count_by_reason'>> {
  suppressed_recall_event_count_by_reason: Record<string, number>;
}

export interface AccountView {
  account_label: string;
  machine_count: number;
  model_usage_totals: ModelUsageTotals;
  token_totals: TokenTotals;
  daily_total_tokens: Record<string, number>;
  memory_recall_savings: AggregatedMemoryRecallSavings;
  otel_metrics: AggregatedOtelMetrics;
  first_session_date: string | null;
  last_computed_date: string | null;
}

export interface UsageSummary {
  account_count: number;
  machine_count: number;
  token_totals: TokenTotals;
  memory_recall_savings: AggregatedMemoryRecallSavings;
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

export type { MemoryRecallSavings, ModelUsageTotals, OtelMetrics };
