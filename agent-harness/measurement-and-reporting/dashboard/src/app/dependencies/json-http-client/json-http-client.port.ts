import { InjectionToken } from '@angular/core';

export interface JsonHttpResponse {
  ok: boolean;
  status: number;
  body: unknown;
}

export interface JsonHttpClientPort {
  getJson(url: string): Promise<JsonHttpResponse>;
}

export const JSON_HTTP_CLIENT = new InjectionToken<JsonHttpClientPort>('JSON_HTTP_CLIENT');
