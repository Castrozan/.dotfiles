import { TestBed } from '@angular/core/testing';
import {
  JSON_HTTP_CLIENT,
  type JsonHttpClientPort,
  type JsonHttpResponse,
} from '../dependencies/json-http-client/json-http-client.port';
import { UsageSnapshotClientService } from './usage-snapshot-client.service';

class RecordingJsonHttpClient implements JsonHttpClientPort {
  readonly requestedUrls: string[] = [];

  constructor(private readonly responsesByUrlFragment: Map<string, JsonHttpResponse>) {}

  async getJson(url: string): Promise<JsonHttpResponse> {
    if (this.requestedUrls.includes(url)) {
      throw new Error('Unexpected repeated HTTP request');
    }
    this.requestedUrls.push(url);
    for (const [fragment, response] of this.responsesByUrlFragment) {
      if (url.includes(fragment)) {
        return response;
      }
    }
    return { ok: false, status: 404, body: null };
  }
}

function okResponse(body: unknown): JsonHttpResponse {
  return { ok: true, status: 200, body };
}

function buildService(responses: Map<string, JsonHttpResponse>) {
  const jsonHttpClient = new RecordingJsonHttpClient(responses);
  TestBed.configureTestingModule({
    providers: [{ provide: JSON_HTTP_CLIENT, useValue: jsonHttpClient }],
  });
  return { service: TestBed.inject(UsageSnapshotClientService), jsonHttpClient };
}

describe('UsageSnapshotClientService', () => {
  it('follows every listing page and skips non-json objects', async () => {
    const responses = new Map<string, JsonHttpResponse>([
      [
        'pageToken=second',
        okResponse({ items: [{ name: 'usage/b.json' }, { name: 'usage/notes.txt' }] }),
      ],
      ['/o?', okResponse({ items: [{ name: 'usage/a.json' }], nextPageToken: 'second' })],
      ['usage%2Fa.json', okResponse({ account_label: 'a' })],
      ['usage%2Fb.json', okResponse({ account_label: 'b' })],
    ]);
    const { service } = buildService(responses);

    const snapshots = await service.fetchAllSnapshots();

    expect(snapshots.map((snapshot) => snapshot.account_label)).toEqual(['a', 'b']);
  });

  it('drops snapshot objects the transport could not fetch', async () => {
    const responses = new Map<string, JsonHttpResponse>([
      ['/o?', okResponse({ items: [{ name: 'usage/a.json' }, { name: 'usage/gone.json' }] })],
      ['usage%2Fa.json', okResponse({ account_label: 'a' })],
      ['usage%2Fgone.json', { ok: false, status: 403, body: null }],
    ]);
    const { service } = buildService(responses);

    const snapshots = await service.fetchAllSnapshots();

    expect(snapshots.length).toBe(1);
  });

  it('raises when the listing request itself fails', async () => {
    const responses = new Map<string, JsonHttpResponse>([
      ['/o?', { ok: false, status: 500, body: null }],
    ]);
    const { service } = buildService(responses);

    await expect(service.fetchAllSnapshots()).rejects.toThrow('status 500');
  });

  it.each([
    ['null response', null],
    ['array response', []],
    ['boolean response', true],
    ['null items', { items: null }],
    ['object items', { items: {} }],
    ['null item', { items: [null] }],
    ['missing object name', { items: [{}] }],
    ['numeric object name', { items: [{ name: 7 }] }],
    ['numeric page token', { nextPageToken: 7 }],
  ])('rejects a listing with %s', async (_description, body) => {
    const { service } = buildService(new Map([['/o?', okResponse(body)]]));

    await expect(service.fetchAllSnapshots()).rejects.toThrow('Invalid snapshot listing response');
  });

  it('accepts an empty listing', async () => {
    const { service, jsonHttpClient } = buildService(new Map([['/o?', okResponse({})]]));

    await expect(service.fetchAllSnapshots()).resolves.toEqual([]);
    expect(jsonHttpClient.requestedUrls).toHaveLength(1);
  });

  it.each([
    ['null response', null],
    ['array response', []],
    ['string response', 'invalid'],
    ['numeric label', { account_label: 7 }],
    ['boolean machine', { machine_label: false }],
    ['string schema version', { schema_version: '1' }],
    ['nonfinite schema version', { schema_version: Infinity }],
    ['array model totals', { model_usage_totals: [] }],
    ['null model totals', { model_usage_totals: { sonnet: null } }],
    ['string token count', { model_usage_totals: { sonnet: { input_tokens: '5' } } }],
    ['object daily usage', { daily_model_tokens: {} }],
    ['null daily entry', { daily_model_tokens: [null] }],
    ['missing daily date', { daily_model_tokens: [{ tokens_by_model: {} }] }],
    ['numeric date', { daily_model_tokens: [{ date: 7, tokens_by_model: {} }] }],
    ['missing daily counts', { daily_model_tokens: [{ date: '2026-10-16' }] }],
    ['array daily counts', { daily_model_tokens: [{ date: '2026-10-16', tokens_by_model: [] }] }],
    [
      'string daily count',
      { daily_model_tokens: [{ date: '2026-10-16', tokens_by_model: { sonnet: '5' } }] },
    ],
    ['string OTEL flag', { otel_metrics: { has_data: 'true' } }],
    ['string OTEL cost', { otel_metrics: { total_cost_usd: '1' } }],
    ['string OTEL count', { otel_metrics: { token_usage_by_type: { input: '5' } } }],
    ['numeric first date', { stats_first_session_date: 7 }],
    ['boolean last date', { stats_last_computed_date: false }],
  ])('drops a snapshot with %s while retaining valid snapshots', async (_description, body) => {
    const responses = new Map<string, JsonHttpResponse>([
      ['/o?', okResponse({ items: [{ name: 'good.json' }, { name: 'bad.json' }] })],
      ['good.json', okResponse({ account_label: 'good' })],
      ['bad.json', okResponse(body)],
    ]);
    const { service } = buildService(responses);

    await expect(service.fetchAllSnapshots()).resolves.toEqual([{ account_label: 'good' }]);
  });

  it.each([
    {},
    { model_usage_totals: {}, daily_model_tokens: [], otel_metrics: { has_data: false } },
    { stats_first_session_date: null, stats_last_computed_date: null },
  ])('accepts optional snapshot fields in %j', async (snapshot) => {
    const { service } = buildService(
      new Map([
        ['/o?', okResponse({ items: [{ name: 'usage.json' }] })],
        ['usage.json', okResponse(snapshot)],
      ]),
    );

    await expect(service.fetchAllSnapshots()).resolves.toEqual([snapshot]);
  });

  it('accepts nested usage metrics, nullable dates and additional metadata', async () => {
    const snapshot = {
      account_label: 'account',
      machine_label: 'machine',
      schema_version: 1,
      model_usage_totals: { sonnet: { input_tokens: 5, output_tokens: 2, cost_usd: 0.1 } },
      daily_model_tokens: [{ date: '2026-10-16', tokens_by_model: { sonnet: 7 } }],
      otel_metrics: { token_usage_by_type: { input: 5 }, total_cost_usd: 0.1, has_data: true },
      stats_first_session_date: null,
      stats_last_computed_date: '2026-10-16',
      additional_metadata: { source: 'snapshot publisher' },
    };
    const { service } = buildService(
      new Map<string, JsonHttpResponse>([
        ['/o?', okResponse({ items: [{ name: 'usage.json' }] })],
        ['usage.json', okResponse(snapshot)],
      ]),
    );

    await expect(service.fetchAllSnapshots()).resolves.toEqual([snapshot]);
  });

  it('drops an individual snapshot when JSON decoding fails', async () => {
    const { service, jsonHttpClient } = buildService(new Map());
    vi.spyOn(jsonHttpClient, 'getJson')
      .mockResolvedValueOnce(okResponse({ items: [{ name: 'broken.json' }] }))
      .mockRejectedValueOnce(new SyntaxError('Invalid JSON'));

    await expect(service.fetchAllSnapshots()).resolves.toEqual([]);
  });
});
