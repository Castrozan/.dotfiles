import { TestBed } from '@angular/core/testing';
import {
  JSON_HTTP_CLIENT,
  JsonHttpClientPort,
  JsonHttpResponse,
} from '../dependencies/json-http-client/json-http-client.port';
import { UsageSnapshotClientService } from './usage-snapshot-client.service';

class RecordingJsonHttpClient implements JsonHttpClientPort {
  readonly requestedUrls: string[] = [];

  constructor(private readonly responsesByUrlFragment: Map<string, JsonHttpResponse<unknown>>) {}

  async getJson<TBody>(url: string): Promise<JsonHttpResponse<TBody>> {
    this.requestedUrls.push(url);
    for (const [fragment, response] of this.responsesByUrlFragment) {
      if (url.includes(fragment)) {
        return response as JsonHttpResponse<TBody>;
      }
    }
    return { ok: false, status: 404, body: null };
  }
}

function okResponse<TBody>(body: TBody): JsonHttpResponse<TBody> {
  return { ok: true, status: 200, body };
}

function buildService(responses: Map<string, JsonHttpResponse<unknown>>) {
  const jsonHttpClient = new RecordingJsonHttpClient(responses);
  TestBed.configureTestingModule({
    providers: [{ provide: JSON_HTTP_CLIENT, useValue: jsonHttpClient }],
  });
  return { service: TestBed.inject(UsageSnapshotClientService), jsonHttpClient };
}

describe('UsageSnapshotClientService', () => {
  it('follows every listing page and skips non-json objects', async () => {
    const responses = new Map<string, JsonHttpResponse<unknown>>([
      [
        'pageToken=second',
        okResponse({ items: [{ name: 'usage/b.json' }, { name: 'usage/notes.txt' }] }),
      ],
      [
        '/storage/v1/b/',
        okResponse({ items: [{ name: 'usage/a.json' }], nextPageToken: 'second' }),
      ],
      ['usage/a.json', okResponse({ account_label: 'a' })],
      ['usage/b.json', okResponse({ account_label: 'b' })],
    ]);
    const { service } = buildService(responses);

    const snapshots = await service.fetchAllSnapshots();

    expect(
      snapshots.map((snapshot) => (snapshot as { account_label: string }).account_label),
    ).toEqual(['a', 'b']);
  });

  it('drops snapshot objects the transport could not fetch', async () => {
    const responses = new Map<string, JsonHttpResponse<unknown>>([
      [
        '/storage/v1/b/',
        okResponse({ items: [{ name: 'usage/a.json' }, { name: 'usage/gone.json' }] }),
      ],
      ['usage/a.json', okResponse({ account_label: 'a' })],
      ['usage/gone.json', { ok: false, status: 403, body: null }],
    ]);
    const { service } = buildService(responses);

    const snapshots = await service.fetchAllSnapshots();

    expect(snapshots.length).toBe(1);
  });

  it('raises when the listing request itself fails', async () => {
    const responses = new Map<string, JsonHttpResponse<unknown>>([
      ['/storage/v1/b/', { ok: false, status: 500, body: null }],
    ]);
    const { service } = buildService(responses);

    await expect(service.fetchAllSnapshots()).rejects.toThrow('status 500');
  });
});
