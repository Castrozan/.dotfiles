import { OtelMetrics } from '../../models/usage-snapshot.model';
import { AggregatedOtelMetrics } from '../../models/account-view.model';

function accumulateTokenUsage(
  accumulated: Record<string, number>,
  tokenUsageByType: Record<string, number>,
): void {
  for (const [tokenType, tokenCount] of Object.entries(tokenUsageByType)) {
    accumulated[tokenType] = (accumulated[tokenType] ?? 0) + tokenCount;
  }
}

export function sumOtelMetrics(otelMetricsList: OtelMetrics[]): AggregatedOtelMetrics {
  const tokenUsageByType: Record<string, number> = {};
  let totalCostUsd = 0;
  for (const otelMetrics of otelMetricsList) {
    accumulateTokenUsage(tokenUsageByType, otelMetrics.token_usage_by_type ?? {});
    totalCostUsd += otelMetrics.total_cost_usd ?? 0;
  }
  return {
    token_usage_by_type: tokenUsageByType,
    total_cost_usd: Math.round(totalCostUsd * 10000) / 10000,
    has_data: Object.keys(tokenUsageByType).length > 0 || totalCostUsd > 0,
  };
}
