import {
  isJsonObject,
  isNumericRecord,
  isOptionalNumber,
  isOptionalString,
} from './json-value-guards';
import type {
  DailyModelTokens,
  ModelTokenTotals,
  ModelUsageTotals,
  OtelMetrics,
  UsageSnapshot,
} from './usage-snapshot.model';

function isModelTokenTotals(value: unknown): value is ModelTokenTotals {
  return isJsonObject(value) && Object.values(value).every(isOptionalNumber);
}

function isModelUsageTotals(value: unknown): value is ModelUsageTotals | undefined {
  return (
    value === undefined || (isJsonObject(value) && Object.values(value).every(isModelTokenTotals))
  );
}

function isDailyModelTokens(value: unknown): value is DailyModelTokens {
  if (!isJsonObject(value)) {
    return false;
  }
  const { date, tokens_by_model: tokensByModel } = value;
  return typeof date === 'string' && isNumericRecord(tokensByModel);
}

function isDailyModelTokenList(value: unknown): value is DailyModelTokens[] | undefined {
  return value === undefined || (Array.isArray(value) && value.every(isDailyModelTokens));
}

function hasValidOtelAmounts(value: Record<string, unknown>): boolean {
  const { token_usage_by_type: tokenUsageByType, total_cost_usd: totalCostUsd } = value;
  return (
    (tokenUsageByType === undefined || isNumericRecord(tokenUsageByType)) &&
    isOptionalNumber(totalCostUsd)
  );
}

function isOtelMetrics(value: unknown): value is OtelMetrics | undefined {
  if (value === undefined) {
    return true;
  }
  if (!isJsonObject(value)) {
    return false;
  }
  const { has_data: hasData } = value;
  return hasValidOtelAmounts(value) && (hasData === undefined || typeof hasData === 'boolean');
}

function hasValidSnapshotLabels(value: Record<string, unknown>): boolean {
  const {
    account_label: accountLabel,
    machine_label: machineLabel,
    schema_version: schemaVersion,
  } = value;
  return (
    isOptionalString(accountLabel) &&
    isOptionalString(machineLabel) &&
    isOptionalNumber(schemaVersion)
  );
}

function hasValidSnapshotDates(value: Record<string, unknown>): boolean {
  const { stats_first_session_date: firstSessionDate, stats_last_computed_date: lastComputedDate } =
    value;
  return (
    (firstSessionDate === null || isOptionalString(firstSessionDate)) &&
    (lastComputedDate === null || isOptionalString(lastComputedDate))
  );
}

function hasValidSnapshotUsage(value: Record<string, unknown>): boolean {
  const {
    model_usage_totals: modelUsageTotals,
    daily_model_tokens: dailyModelTokens,
    otel_metrics: otelMetrics,
  } = value;
  return (
    isModelUsageTotals(modelUsageTotals) &&
    isDailyModelTokenList(dailyModelTokens) &&
    isOtelMetrics(otelMetrics)
  );
}

function isUsageSnapshot(value: unknown): value is UsageSnapshot {
  return (
    isJsonObject(value) &&
    hasValidSnapshotLabels(value) &&
    hasValidSnapshotDates(value) &&
    hasValidSnapshotUsage(value)
  );
}

export function parseUsageSnapshot(value: unknown): UsageSnapshot {
  if (!isUsageSnapshot(value)) {
    throw new Error('Invalid usage snapshot response');
  }
  return value;
}
