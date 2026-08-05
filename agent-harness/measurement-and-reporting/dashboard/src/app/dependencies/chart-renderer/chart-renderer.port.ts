import { InjectionToken } from '@angular/core';

export interface LineChartSeries {
  label: string;
  values: (number | null)[];
  colorHex: string;
}

export interface LineChartDefinition {
  title: string;
  labels: string[];
  series: LineChartSeries[];
}

export interface RenderedChart {
  destroy(): void;
}

export interface ChartRendererPort {
  renderLineChart(canvas: HTMLCanvasElement, definition: LineChartDefinition): RenderedChart;
}

export const CHART_RENDERER = new InjectionToken<ChartRendererPort>('CHART_RENDERER');
