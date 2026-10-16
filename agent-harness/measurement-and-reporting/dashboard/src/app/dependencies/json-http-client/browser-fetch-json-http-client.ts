import { Injectable } from '@angular/core';
import type { JsonHttpClientPort, JsonHttpResponse } from './json-http-client.port';

@Injectable({ providedIn: 'root' })
export class BrowserFetchJsonHttpClient implements JsonHttpClientPort {
  async getJson(url: string): Promise<JsonHttpResponse> {
    const response = await fetch(url, { cache: 'no-store' });
    if (!response.ok) {
      return { ok: false, status: response.status, body: null };
    }
    return {
      ok: true,
      status: response.status,
      body: await response.json(),
    };
  }
}
