import {
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  effect,
  input,
  viewChild,
} from '@angular/core';
import { Chart } from 'chart.js/auto';
import { ChartSeries } from '../../models/account-view.model';
import { ACCOUNT_SERIES_COLORS } from '../../shared/token-formatting';

@Component({
  selector: 'app-daily-tokens-chart',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `<div class="chart-wrap"><canvas #chartCanvas></canvas></div>`,
})
export class DailyTokensChartComponent {
  readonly chart = input.required<ChartSeries>();

  private readonly chartCanvas = viewChild.required<ElementRef<HTMLCanvasElement>>('chartCanvas');
  private renderedChart: Chart | null = null;

  constructor() {
    effect(() => {
      const chartSeries = this.chart();
      const canvas = this.chartCanvas().nativeElement;
      this.renderedChart?.destroy();
      this.renderedChart = new Chart(canvas, {
        type: 'line',
        data: {
          labels: chartSeries.dates,
          datasets: chartSeries.series.map((accountSeries, seriesIndex) => {
            const color = ACCOUNT_SERIES_COLORS[seriesIndex % ACCOUNT_SERIES_COLORS.length];
            return {
              label: accountSeries.account_label,
              data: accountSeries.values,
              borderColor: color,
              backgroundColor: `${color}26`,
              tension: 0.2,
              spanGaps: true,
              pointRadius: 2,
            };
          }),
        },
        options: {
          plugins: {
            legend: { labels: { color: '#e6edf3' } },
            title: { display: true, text: 'daily tokens per account', color: '#8b949e' },
          },
          scales: {
            y: { ticks: { color: '#8b949e' }, grid: { color: '#21262d' } },
            x: { ticks: { color: '#8b949e' }, grid: { color: '#21262d' } },
          },
        },
      });
    });
  }
}
