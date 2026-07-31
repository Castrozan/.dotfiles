import { MemoryRecallSavings, OtelMetrics } from '../../models/usage-snapshot.model';
import {
  AggregatedMemoryRecallSavings,
  AggregatedOtelMetrics,
} from '../../models/account-view.model';

const SCALAR_SAVINGS_FIELDS: (keyof AggregatedMemoryRecallSavings)[] = [
  'memory_recall_session_count',
  'injected_recall_event_count',
  'injected_recall_character_total',
  'suppressed_recall_event_total',
  'dedup_suppressed_character_total',
];

export function sumMemoryRecallSavings(
  memoryRecallSavingsList: MemoryRecallSavings[],
): AggregatedMemoryRecallSavings {
  const summed: AggregatedMemoryRecallSavings = {
    memory_recall_session_count: 0,
    injected_recall_event_count: 0,
    injected_recall_character_total: 0,
    suppressed_recall_event_total: 0,
    dedup_suppressed_character_total: 0,
    suppressed_recall_event_count_by_reason: {},
  };
  for (const memoryRecallSavings of memoryRecallSavingsList) {
    for (const scalarField of SCALAR_SAVINGS_FIELDS) {
      const value = memoryRecallSavings[scalarField as keyof MemoryRecallSavings];
      (summed[scalarField] as number) += (value as number) ?? 0;
    }
    const byReason = memoryRecallSavings.suppressed_recall_event_count_by_reason ?? {};
    for (const [reason, count] of Object.entries(byReason)) {
      summed.suppressed_recall_event_count_by_reason[reason] =
        (summed.suppressed_recall_event_count_by_reason[reason] ?? 0) + count;
    }
  }
  return summed;
}

export function sumOtelMetrics(otelMetricsList: OtelMetrics[]): AggregatedOtelMetrics {
  const tokenUsageByType: Record<string, number> = {};
  let totalCostUsd = 0;
  for (const otelMetrics of otelMetricsList) {
    for (const [tokenType, tokenCount] of Object.entries(otelMetrics.token_usage_by_type ?? {})) {
      tokenUsageByType[tokenType] = (tokenUsageByType[tokenType] ?? 0) + tokenCount;
    }
    totalCostUsd += otelMetrics.total_cost_usd ?? 0;
  }
  return {
    token_usage_by_type: tokenUsageByType,
    total_cost_usd: Math.round(totalCostUsd * 10000) / 10000,
    has_data: Object.keys(tokenUsageByType).length > 0 || totalCostUsd > 0,
  };
}
