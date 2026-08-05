import {
  ApplicationConfig,
  provideBrowserGlobalErrorListeners,
  provideZonelessChangeDetection,
} from '@angular/core';
import { ChartJsChartRenderer } from './dependencies/chart-renderer/chart-js-chart-renderer';
import { CHART_RENDERER } from './dependencies/chart-renderer/chart-renderer.port';
import { BrowserFetchJsonHttpClient } from './dependencies/json-http-client/browser-fetch-json-http-client';
import { JSON_HTTP_CLIENT } from './dependencies/json-http-client/json-http-client.port';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideZonelessChangeDetection(),
    { provide: CHART_RENDERER, useExisting: ChartJsChartRenderer },
    { provide: JSON_HTTP_CLIENT, useExisting: BrowserFetchJsonHttpClient },
  ],
};
