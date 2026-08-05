import {
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  effect,
  inject,
  input,
  viewChild,
} from '@angular/core';
import {
  CHART_RENDERER,
  LineChartDefinition,
  RenderedChart,
} from '../../dependencies/chart-renderer/chart-renderer.port';
import { ChartSeries } from '../../models/account-view.model';
import { ACCOUNT_SERIES_COLORS } from '../../shared/token-formatting';

const DAILY_TOKENS_CHART_TITLE = 'daily tokens per account';

export function toLineChartDefinition(chartSeries: ChartSeries): LineChartDefinition {
  return {
    title: DAILY_TOKENS_CHART_TITLE,
    labels: chartSeries.dates,
    series: chartSeries.series.map((accountSeries, seriesIndex) => ({
      label: accountSeries.account_label,
      values: accountSeries.values,
      colorHex: ACCOUNT_SERIES_COLORS[seriesIndex % ACCOUNT_SERIES_COLORS.length],
    })),
  };
}

@Component({
  selector: 'app-daily-tokens-chart',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `<div class="chart-wrap"><canvas #chartCanvas></canvas></div>`,
})
export class DailyTokensChartComponent {
  readonly chart = input.required<ChartSeries>();

  private readonly chartRenderer = inject(CHART_RENDERER);
  private readonly chartCanvas = viewChild.required<ElementRef<HTMLCanvasElement>>('chartCanvas');
  private renderedChart: RenderedChart | null = null;

  constructor() {
    effect(() => {
      const definition = toLineChartDefinition(this.chart());
      this.renderedChart?.destroy();
      this.renderedChart = this.chartRenderer.renderLineChart(
        this.chartCanvas().nativeElement,
        definition,
      );
    });
  }
}
