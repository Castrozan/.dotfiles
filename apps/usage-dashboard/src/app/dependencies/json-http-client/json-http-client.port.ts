import { InjectionToken } from '@angular/core';

export interface JsonHttpResponse<TBody> {
  ok: boolean;
  status: number;
  body: TBody | null;
}

export interface JsonHttpClientPort {
  getJson<TBody>(url: string): Promise<JsonHttpResponse<TBody>>;
}

export const JSON_HTTP_CLIENT = new InjectionToken<JsonHttpClientPort>('JSON_HTTP_CLIENT');
