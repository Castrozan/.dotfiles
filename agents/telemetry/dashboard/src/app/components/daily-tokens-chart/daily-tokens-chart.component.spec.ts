import { ChartSeries } from '../../models/account-view.model';
import { ACCOUNT_SERIES_COLORS } from '../../shared/token-formatting';
import { toLineChartDefinition } from './daily-tokens-chart.component';

function buildChartSeries(accountCount: number): ChartSeries {
  return {
    dates: ['2026-07-01', '2026-07-02'],
    series: Array.from({ length: accountCount }, (_, index) => ({
      account_label: `account-${index}`,
      values: [index, null],
    })),
  };
}

describe('toLineChartDefinition', () => {
  it('maps domain series onto a renderer-agnostic definition', () => {
    const definition = toLineChartDefinition(buildChartSeries(2));

    expect(definition.title).toBe('daily tokens per account');
    expect(definition.labels).toEqual(['2026-07-01', '2026-07-02']);
    expect(definition.series.map((series) => series.label)).toEqual(['account-0', 'account-1']);
    expect(definition.series[1].values).toEqual([1, null]);
  });

  it('cycles the palette once there are more accounts than colours', () => {
    const definition = toLineChartDefinition(buildChartSeries(ACCOUNT_SERIES_COLORS.length + 1));

    expect(definition.series[0].colorHex).toBe(ACCOUNT_SERIES_COLORS[0]);
    expect(definition.series[ACCOUNT_SERIES_COLORS.length].colorHex).toBe(ACCOUNT_SERIES_COLORS[0]);
  });
});
