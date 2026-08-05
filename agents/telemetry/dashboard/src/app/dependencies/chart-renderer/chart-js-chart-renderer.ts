import { Injectable } from '@angular/core';
import { Chart } from 'chart.js/auto';
import { ChartRendererPort, LineChartDefinition, RenderedChart } from './chart-renderer.port';

const LEGEND_TEXT_COLOR = '#e6edf3';
const AXIS_TEXT_COLOR = '#8b949e';
const GRID_LINE_COLOR = '#21262d';
const SERIES_FILL_ALPHA_SUFFIX = '26';

@Injectable({ providedIn: 'root' })
export class ChartJsChartRenderer implements ChartRendererPort {
  renderLineChart(canvas: HTMLCanvasElement, definition: LineChartDefinition): RenderedChart {
    return new Chart(canvas, {
      type: 'line',
      data: {
        labels: definition.labels,
        datasets: definition.series.map((series) => ({
          label: series.label,
          data: series.values,
          borderColor: series.colorHex,
          backgroundColor: `${series.colorHex}${SERIES_FILL_ALPHA_SUFFIX}`,
          tension: 0.2,
          spanGaps: true,
          pointRadius: 2,
        })),
      },
      options: {
        plugins: {
          legend: { labels: { color: LEGEND_TEXT_COLOR } },
          title: { display: true, text: definition.title, color: AXIS_TEXT_COLOR },
        },
        scales: {
          y: { ticks: { color: AXIS_TEXT_COLOR }, grid: { color: GRID_LINE_COLOR } },
          x: { ticks: { color: AXIS_TEXT_COLOR }, grid: { color: GRID_LINE_COLOR } },
        },
      },
    });
  }
}
