import { sumOtelMetrics } from './otel-metrics-aggregation';
import { combineDailyTotalTokens, sumModelUsageTotals } from './token-aggregation';

describe('usage aggregation functions', () => {
  it('returns empty totals without input', () => {
    expect(sumModelUsageTotals([])).toEqual({});
    expect(combineDailyTotalTokens([])).toEqual({});
    expect(sumOtelMetrics([])).toEqual({
      token_usage_by_type: {},
      total_cost_usd: 0,
      has_data: false,
    });
  });

  it('combines repeated models and missing fields without mutating snapshots', () => {
    const first = { model: { input_tokens: 12, cost_usd: 0.25 } };
    const second = { model: { input_tokens: 8, output_tokens: undefined }, other: {} };
    expect(sumModelUsageTotals([first, {}, second])).toEqual({
      model: { input_tokens: 20, cost_usd: 0.25, output_tokens: 0 },
      other: {},
    });
    expect(first).toEqual({ model: { input_tokens: 12, cost_usd: 0.25 } });
    expect(second.model.output_tokens).toBeUndefined();
  });

  it('adds duplicate dates and ignores entries without a date', () => {
    expect(
      combineDailyTotalTokens([
        [
          { date: '2026-10-03', tokens_by_model: { first: 12, second: 8 } },
          { date: '', tokens_by_model: { first: 1000 } },
        ],
        [],
        [
          { date: '2026-10-03', tokens_by_model: { first: 5 } },
          { date: '2026-10-04', tokens_by_model: {} },
        ],
      ]),
    ).toEqual({ '2026-10-03': 25, '2026-10-04': 0 });
  });

  it('sums partial telemetry and rounds cost only after accumulation', () => {
    expect(
      sumOtelMetrics([
        {},
        { token_usage_by_type: { input: 12, output: 0 }, total_cost_usd: 0.00006 },
        { token_usage_by_type: { input: 8 }, total_cost_usd: 0.00006 },
      ]),
    ).toEqual({
      token_usage_by_type: { input: 20, output: 0 },
      total_cost_usd: 0.0001,
      has_data: true,
    });
    expect(sumOtelMetrics([{ total_cost_usd: 0.1 }]).has_data).toBe(true);
    expect(sumOtelMetrics([{}]).has_data).toBe(false);
  });
});
