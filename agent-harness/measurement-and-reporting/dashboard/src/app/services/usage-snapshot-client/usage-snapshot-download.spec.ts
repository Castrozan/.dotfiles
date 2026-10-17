import {
  buildRecordingSnapshotClientService,
  listingOf,
  okResponse,
  singleListingPage,
} from './storage-json-http-client-doubles';

describe('UsageSnapshotClientService snapshot download', () => {
  it('requests reserved object names through the fully encoded JSON API media endpoint', async () => {
    const encodedSegmentsByObjectName = new Map([
      ['snapshots/a b.json', 'snapshots%2Fa%20b.json'],
      ['snapshots/naïve-日本.json', 'snapshots%2Fna%C3%AFve-%E6%97%A5%E6%9C%AC.json'],
      ['snapshots/100%.json', 'snapshots%2F100%25.json'],
      ['snapshots/why?.json', 'snapshots%2Fwhy%3F.json'],
      ['snapshots/frag#ment.json', 'snapshots%2Ffrag%23ment.json'],
      ["snapshots/it's(1)*!.json", 'snapshots%2Fit%27s%281%29%2A%21.json'],
      ['snapshots/a+b&c=d;e,f:g@h$i.json', 'snapshots%2Fa%2Bb%26c%3Dd%3Be%2Cf%3Ag%40h%24i.json'],
    ]);
    const objectNames = [...encodedSegmentsByObjectName.keys()];
    const { service, jsonHttpClient } = buildRecordingSnapshotClientService(
      singleListingPage(listingOf(...objectNames)),
      new Map(objectNames.map((name) => [name, okResponse({ account_label: name })])),
    );

    const snapshots = await service.fetchAllSnapshots();

    expect(jsonHttpClient.requestedUrls.slice(1)).toEqual(
      [...encodedSegmentsByObjectName.values()].map(
        (encodedSegment) =>
          `https://storage.googleapis.com/storage/v1/b/zg-url-shortener-2026-dotfiles-usage-snapshots/o/${encodedSegment}?alt=media`,
      ),
    );
    expect(snapshots.map((snapshot) => snapshot.account_label)).toEqual(objectNames);
  });

  it('skips an object name that cannot be encoded while retaining valid snapshots', async () => {
    const { service } = buildRecordingSnapshotClientService(
      singleListingPage(listingOf('\ud800.json', 'good.json')),
      new Map([['good.json', okResponse({ account_label: 'good' })]]),
    );

    await expect(service.fetchAllSnapshots()).resolves.toEqual([{ account_label: 'good' }]);
  });

  it('drops snapshot objects the transport could not fetch', async () => {
    const { service } = buildRecordingSnapshotClientService(
      singleListingPage(listingOf('usage/a.json', 'usage/gone.json')),
      new Map([
        ['usage/a.json', okResponse({ account_label: 'a' })],
        ['usage/gone.json', { ok: false, status: 403, body: null }],
      ]),
    );

    const snapshots = await service.fetchAllSnapshots();

    expect(snapshots.length).toBe(1);
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
    const { service } = buildRecordingSnapshotClientService(
      singleListingPage(listingOf('good.json', 'bad.json')),
      new Map([
        ['good.json', okResponse({ account_label: 'good' })],
        ['bad.json', okResponse(body)],
      ]),
    );

    await expect(service.fetchAllSnapshots()).resolves.toEqual([{ account_label: 'good' }]);
  });

  it.each([
    {},
    { model_usage_totals: {}, daily_model_tokens: [], otel_metrics: { has_data: false } },
    { stats_first_session_date: null, stats_last_computed_date: null },
  ])('accepts optional snapshot fields in %j', async (snapshot) => {
    const { service } = buildRecordingSnapshotClientService(
      singleListingPage(listingOf('usage.json')),
      new Map([['usage.json', okResponse(snapshot)]]),
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
    const { service } = buildRecordingSnapshotClientService(
      singleListingPage(listingOf('usage.json')),
      new Map([['usage.json', okResponse(snapshot)]]),
    );

    await expect(service.fetchAllSnapshots()).resolves.toEqual([snapshot]);
  });

  it('drops an individual snapshot when JSON decoding fails', async () => {
    const { service, jsonHttpClient } = buildRecordingSnapshotClientService(new Map());
    vi.spyOn(jsonHttpClient, 'getJson')
      .mockResolvedValueOnce(okResponse(listingOf('broken.json')))
      .mockRejectedValueOnce(new SyntaxError('Invalid JSON'));

    await expect(service.fetchAllSnapshots()).resolves.toEqual([]);
  });
});
