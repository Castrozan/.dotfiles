import { UsageAggregationService } from './usage-aggregation.service';
import { UsageSnapshot } from '../../models/usage-snapshot.model';

function buildService(): UsageAggregationService {
  return new UsageAggregationService();
}

const firstMachineSnapshot: UsageSnapshot = {
  account_label: 'acct-a',
  machine_label: 'machine-1',
  model_usage_totals: {
    'claude-opus': {
      input_tokens: 100,
      output_tokens: 50,
      cache_read_input_tokens: 900,
      cache_creation_input_tokens: 0,
      cost_usd: 2,
    },
  },
  daily_model_tokens: [{ date: '2026-06-01', tokens_by_model: { 'claude-opus': 300 } }],
  memory_recall_savings: {
    suppressed_recall_event_total: 5,
    dedup_suppressed_character_total: 40,
    suppressed_recall_event_count_by_reason: { dedup: 5 },
  },
  otel_metrics: { token_usage_by_type: { cacheRead: 900 }, total_cost_usd: 1.5 },
  stats_first_session_date: '2026-05-26',
  stats_last_computed_date: '2026-06-10',
};

const secondMachineSnapshot: UsageSnapshot = {
  account_label: 'acct-a',
  machine_label: 'machine-2',
  model_usage_totals: {
    'claude-opus': {
      input_tokens: 0,
      output_tokens: 10,
      cache_read_input_tokens: 100,
      cache_creation_input_tokens: 0,
      cost_usd: 1,
    },
  },
  daily_model_tokens: [{ date: '2026-06-02', tokens_by_model: { 'claude-opus': 200 } }],
  memory_recall_savings: {
    suppressed_recall_event_total: 3,
    suppressed_recall_event_count_by_reason: { budget: 3 },
  },
  otel_metrics: { token_usage_by_type: { cacheRead: 100 }, total_cost_usd: 0.5 },
  stats_first_session_date: '2026-05-20',
  stats_last_computed_date: '2026-06-12',
};

const otherAccountSnapshot: UsageSnapshot = {
  account_label: 'acct-b',
  machine_label: 'machine-3',
  model_usage_totals: {
    'claude-haiku': { output_tokens: 5, cache_read_input_tokens: 10, cost_usd: 0 },
  },
  daily_model_tokens: [{ date: '2026-06-01', tokens_by_model: { 'claude-haiku': 70 } }],
  otel_metrics: {},
  stats_first_session_date: '2026-06-01',
  stats_last_computed_date: '2026-06-11',
};

describe('UsageAggregationService', () => {
  it('groups snapshots per account and sums token totals', () => {
    const accounts = buildService().groupSnapshotsByAccount([
      firstMachineSnapshot,
      secondMachineSnapshot,
    ]);
    expect(accounts).toHaveLength(1);
    expect(accounts[0].machine_count).toBe(2);
    expect(accounts[0].token_totals.cache_read_input_tokens).toBe(1000);
    expect(accounts[0].token_totals.cost_usd).toBe(3);
    expect(accounts[0].first_session_date).toBe('2026-05-20');
    expect(accounts[0].last_computed_date).toBe('2026-06-12');
    expect(accounts[0].otel_metrics.token_usage_by_type['cacheRead']).toBe(1000);
    expect(accounts[0].otel_metrics.total_cost_usd).toBe(2);
  });

  it('aligns the chart series across the union of dates with null gaps', () => {
    const service = buildService();
    const accounts = service.groupSnapshotsByAccount([
      firstMachineSnapshot,
      secondMachineSnapshot,
      otherAccountSnapshot,
    ]);
    const chart = service.buildChartSeries(accounts);
    expect(chart.dates).toEqual(['2026-06-01', '2026-06-02']);
    const accountA = chart.series.find((series) => series.account_label === 'acct-a');
    expect(accountA?.values).toEqual([300, 200]);
    const accountB = chart.series.find((series) => series.account_label === 'acct-b');
    expect(accountB?.values).toEqual([70, null]);
  });

  it('summarizes across accounts and flags otel data presence', () => {
    const service = buildService();
    const viewModel = service.buildUsageViewModel([
      firstMachineSnapshot,
      secondMachineSnapshot,
      otherAccountSnapshot,
    ]);
    expect(viewModel.summary.account_count).toBe(2);
    expect(viewModel.summary.machine_count).toBe(3);
    expect(viewModel.summary.memory_recall_savings.suppressed_recall_event_total).toBe(8);
    expect(viewModel.summary.memory_recall_savings.suppressed_recall_event_count_by_reason).toEqual(
      { dedup: 5, budget: 3 },
    );
    expect(viewModel.summary.otel_metrics.has_data).toBe(true);
    expect(viewModel.summary.first_session_date).toBe('2026-05-20');
  });
});
