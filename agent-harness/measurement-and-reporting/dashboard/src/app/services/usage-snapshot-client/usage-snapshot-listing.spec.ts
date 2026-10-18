import {
  FIRST_LISTING_PAGE,
  buildRecordingSnapshotClientService,
  listingOf,
  okResponse,
  singleListingPage,
} from './storage-json-http-client-doubles';

describe('UsageSnapshotClientService listing', () => {
  it('follows every listing page and skips non-json objects', async () => {
    const { service } = buildRecordingSnapshotClientService(
      new Map([
        [FIRST_LISTING_PAGE, okResponse({ ...listingOf('usage/a.json'), nextPageToken: 'second' })],
        ['second', okResponse(listingOf('usage/b.json', 'usage/notes.txt'))],
      ]),
      new Map([
        ['usage/a.json', okResponse({ account_label: 'a' })],
        ['usage/b.json', okResponse({ account_label: 'b' })],
      ]),
    );

    const snapshots = await service.fetchAllSnapshots();

    expect(snapshots.map((snapshot) => snapshot.account_label)).toEqual(['a', 'b']);
  });

  it('downloads each object named on several listing pages once in first-seen order', async () => {
    const { service, jsonHttpClient } = buildRecordingSnapshotClientService(
      new Map([
        [
          FIRST_LISTING_PAGE,
          okResponse({ ...listingOf('a.json', 'b.json', 'a.json'), nextPageToken: 'p2' }),
        ],
        ['p2', okResponse({ ...listingOf('c.json', 'b.json'), nextPageToken: 'p3' })],
        ['p3', okResponse(listingOf('a.json', 'd.json', 'c.json'))],
      ]),
      new Map(
        ['a', 'b', 'c', 'd'].map((label) => [
          `${label}.json`,
          okResponse({ account_label: label }),
        ]),
      ),
    );

    const snapshots = await service.fetchAllSnapshots();

    expect(jsonHttpClient.requestedObjectNames()).toEqual(['a.json', 'b.json', 'c.json', 'd.json']);
    expect(snapshots.map((snapshot) => snapshot.account_label)).toEqual(['a', 'b', 'c', 'd']);
  });

  it('raises when the listing request itself fails', async () => {
    const { service } = buildRecordingSnapshotClientService(
      new Map([[FIRST_LISTING_PAGE, { ok: false, status: 500, body: null }]]),
    );

    await expect(service.fetchAllSnapshots()).rejects.toThrow('status 500');
  });

  it('raises when a later listing page fails without downloading any snapshot', async () => {
    const { service, jsonHttpClient } = buildRecordingSnapshotClientService(
      new Map([
        [FIRST_LISTING_PAGE, okResponse({ ...listingOf('a.json'), nextPageToken: 'second' })],
        ['second', { ok: false, status: 503, body: null }],
      ]),
    );

    await expect(service.fetchAllSnapshots()).rejects.toThrow('status 503');
    expect(jsonHttpClient.requestedObjectNames()).toEqual([]);
  });

  it('raises when the listing transport rejects', async () => {
    const { service, jsonHttpClient } = buildRecordingSnapshotClientService(new Map());
    vi.spyOn(jsonHttpClient, 'getJson').mockRejectedValueOnce(new TypeError('Failed to fetch'));

    await expect(service.fetchAllSnapshots()).rejects.toThrow('Failed to fetch');
  });

  it('rejects a page token that names its own page before requesting it again', async () => {
    const { service, jsonHttpClient } = buildRecordingSnapshotClientService(
      new Map([
        [FIRST_LISTING_PAGE, okResponse({ ...listingOf('a.json'), nextPageToken: 'loop' })],
        ['loop', okResponse({ ...listingOf('b.json'), nextPageToken: 'loop' })],
      ]),
    );

    await expect(service.fetchAllSnapshots()).rejects.toThrow(
      'snapshot listing pagination cycle: page token "loop" was already requested',
    );
    expect(jsonHttpClient.requestedUrls).toHaveLength(2);
    expect(jsonHttpClient.requestedObjectNames()).toEqual([]);
  });

  it('rejects a cycle across several page tokens before requesting a page again', async () => {
    const { service, jsonHttpClient } = buildRecordingSnapshotClientService(
      new Map([
        [FIRST_LISTING_PAGE, okResponse({ nextPageToken: 'first' })],
        ['first', okResponse({ nextPageToken: 'second' })],
        ['second', okResponse({ nextPageToken: 'third' })],
        ['third', okResponse({ nextPageToken: 'first' })],
      ]),
    );

    await expect(service.fetchAllSnapshots()).rejects.toThrow(
      'snapshot listing pagination cycle: page token "first" was already requested',
    );
    expect(jsonHttpClient.requestedUrls).toHaveLength(4);
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
    const { service } = buildRecordingSnapshotClientService(singleListingPage(body));

    await expect(service.fetchAllSnapshots()).rejects.toThrow('Invalid snapshot listing response');
  });

  it.each([
    ['no fields', {}],
    ['no items', { items: [] }],
    ['an empty page token', { items: [], nextPageToken: '' }],
    ['only non-json objects', listingOf('snapshots/readme.txt')],
  ])('accepts an empty listing with %s', async (_description, body) => {
    const { service, jsonHttpClient } = buildRecordingSnapshotClientService(
      singleListingPage(body),
    );

    await expect(service.fetchAllSnapshots()).resolves.toEqual([]);
    expect(jsonHttpClient.requestedUrls).toHaveLength(1);
  });
});
