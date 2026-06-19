import { Injectable } from '@angular/core';
import { UsageSnapshot } from '../../models/usage-snapshot.model';
import {
  AccountView,
  ChartSeries,
  UsageSummary,
  UsageViewModel,
} from '../../models/account-view.model';
import {
  aggregateTokenFields,
  combineDailyTotalTokens,
  sumModelUsageTotals,
} from './token-aggregation';
import { sumMemoryRecallSavings, sumOtelMetrics } from './savings-aggregation';

function earliest(dateValues: (string | null | undefined)[]): string | null {
  const present = dateValues.filter((value): value is string => Boolean(value)).sort();
  return present.length ? present[0] : null;
}

function latest(dateValues: (string | null | undefined)[]): string | null {
  const present = dateValues.filter((value): value is string => Boolean(value)).sort();
  return present.length ? present[present.length - 1] : null;
}

@Injectable({ providedIn: 'root' })
export class UsageAggregationService {
  groupSnapshotsByAccount(usageSnapshots: UsageSnapshot[]): AccountView[] {
    const snapshotsByAccount = new Map<string, UsageSnapshot[]>();
    for (const usageSnapshot of usageSnapshots) {
      const accountLabel = usageSnapshot.account_label ?? 'unknown';
      const bucket = snapshotsByAccount.get(accountLabel) ?? [];
      bucket.push(usageSnapshot);
      snapshotsByAccount.set(accountLabel, bucket);
    }
    return [...snapshotsByAccount.keys()].sort().map((accountLabel) => {
      const accountSnapshots = snapshotsByAccount.get(accountLabel)!;
      const modelUsageTotals = sumModelUsageTotals(
        accountSnapshots.map((snapshot) => snapshot.model_usage_totals ?? {}),
      );
      return {
        account_label: accountLabel,
        machine_count: new Set(accountSnapshots.map((snapshot) => snapshot.machine_label)).size,
        model_usage_totals: modelUsageTotals,
        token_totals: aggregateTokenFields(modelUsageTotals),
        daily_total_tokens: combineDailyTotalTokens(
          accountSnapshots.map((snapshot) => snapshot.daily_model_tokens ?? []),
        ),
        memory_recall_savings: sumMemoryRecallSavings(
          accountSnapshots.map((snapshot) => snapshot.memory_recall_savings ?? {}),
        ),
        otel_metrics: sumOtelMetrics(
          accountSnapshots.map((snapshot) => snapshot.otel_metrics ?? {}),
        ),
        first_session_date: earliest(
          accountSnapshots.map((snapshot) => snapshot.stats_first_session_date),
        ),
        last_computed_date: latest(
          accountSnapshots.map((snapshot) => snapshot.stats_last_computed_date),
        ),
      };
    });
  }

  buildChartSeries(accountViews: AccountView[]): ChartSeries {
    const chartDates = [
      ...new Set(
        accountViews.flatMap((accountView) => Object.keys(accountView.daily_total_tokens)),
      ),
    ].sort();
    const series = accountViews.map((accountView) => ({
      account_label: accountView.account_label,
      values: chartDates.map((entryDate) =>
        entryDate in accountView.daily_total_tokens
          ? accountView.daily_total_tokens[entryDate]
          : null,
      ),
    }));
    return { dates: chartDates, series };
  }

  summarizeAccounts(accountViews: AccountView[]): UsageSummary {
    const combinedModelUsage = sumModelUsageTotals(
      accountViews.map((accountView) => accountView.model_usage_totals),
    );
    return {
      account_count: accountViews.length,
      machine_count: accountViews.reduce(
        (runningTotal, accountView) => runningTotal + accountView.machine_count,
        0,
      ),
      token_totals: aggregateTokenFields(combinedModelUsage),
      memory_recall_savings: sumMemoryRecallSavings(
        accountViews.map((accountView) => accountView.memory_recall_savings),
      ),
      otel_metrics: sumOtelMetrics(accountViews.map((accountView) => accountView.otel_metrics)),
      first_session_date: earliest(
        accountViews.map((accountView) => accountView.first_session_date),
      ),
      last_computed_date: latest(accountViews.map((accountView) => accountView.last_computed_date)),
    };
  }

  buildUsageViewModel(usageSnapshots: UsageSnapshot[]): UsageViewModel {
    const accountViews = this.groupSnapshotsByAccount(usageSnapshots);
    return {
      accounts: accountViews,
      summary: this.summarizeAccounts(accountViews),
      chart: this.buildChartSeries(accountViews),
    };
  }
}
