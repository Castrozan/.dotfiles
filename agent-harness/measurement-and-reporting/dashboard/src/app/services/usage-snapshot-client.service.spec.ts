import { DASHBOARD_CONFIGURATION } from '../config/dashboard-config';
import {
  buildServiceWithFakeStorage,
  okResponse,
  singlePageListing,
} from './usage-snapshot-client/cloud-storage-json-http-client.doubles';

const objectMediaUrlPrefix = `https://storage.googleapis.com/storage/v1/b/${DASHBOARD_CONFIGURATION.snapshotsBucket}/o/`;

describe('UsageSnapshotClientService', () => {
  it('follows every listing page and skips non-json objects', async () => {
    const { service, jsonHttpClient } = buildServiceWithFakeStorage(
      new Map([
        ['', okResponse({ items: [{ name: 'usage/a.json' }], nextPageToken: 'second' })],
        ['second', okResponse({ items: [{ name: 'usage/b.json' }, { name: 'usage/notes.txt' }] })],
      ]),
      new Map([
        ['usage/a.json', okResponse({ account_label: 'a' })],
        ['usage/b.json', okResponse({ account_label: 'b' })],
      ]),
    );

    const snapshots = await service.fetchAllSnapshots();

    expect(snapshots.map((snapshot) => snapshot.account_label)).toEqual(['a', 'b']);
    expect(jsonHttpClient.requestedPageTokens).toEqual(['', 'second']);
    expect(jsonHttpClient.requestedObjectNames).toEqual(['usage/a.json', 'usage/b.json']);
    expect(new URL(jsonHttpClient.requestedUrls[0]).searchParams.get('prefix')).toBe(
      DASHBOARD_CONFIGURATION.snapshotsObjectPrefix,
    );
  });

  it('drops snapshot objects the transport could not fetch', async () => {
    const { service } = buildServiceWithFakeStorage(
      singlePageListing(['usage/a.json', 'usage/gone.json']),
      new Map([
        ['usage/a.json', okResponse({ account_label: 'a' })],
        ['usage/gone.json', { ok: false, status: 403, body: null }],
      ]),
    );

    const snapshots = await service.fetchAllSnapshots();

    expect(snapshots.length).toBe(1);
  });

  it('raises when the listing request itself fails', async () => {
    const { service } = buildServiceWithFakeStorage(
      new Map([['', { ok: false, status: 500, body: null }]]),
    );

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
    const { service } = buildServiceWithFakeStorage(new Map([['', okResponse(body)]]));

    await expect(service.fetchAllSnapshots()).rejects.toThrow('Invalid snapshot listing response');
  });

  it.each([{}, { items: [] }])('accepts an empty listing %j', async (body) => {
    const { service, jsonHttpClient } = buildServiceWithFakeStorage(
      new Map([['', okResponse(body)]]),
    );

    await expect(service.fetchAllSnapshots()).resolves.toEqual([]);
    expect(jsonHttpClient.requestedUrls).toHaveLength(1);
  });

  it('downloads each object name once across pages in first-seen order', async () => {
    const { service, jsonHttpClient } = buildServiceWithFakeStorage(
      new Map([
        [
          '',
          okResponse({
            items: [{ name: 'usage/a.json' }, { name: 'usage/b.json' }, { name: 'usage/a.json' }],
            nextPageToken: 'second',
          }),
        ],
        [
          'second',
          okResponse({
            items: [{ name: 'usage/b.json' }, { name: 'usage/c.json' }, { name: 'usage/a.json' }],
          }),
        ],
      ]),
      new Map([
        ['usage/a.json', okResponse({ account_label: 'a' })],
        ['usage/b.json', okResponse({ account_label: 'b' })],
        ['usage/c.json', okResponse({ account_label: 'c' })],
      ]),
    );

    const snapshots = await service.fetchAllSnapshots();

    expect(snapshots.map((snapshot) => snapshot.account_label)).toEqual(['a', 'b', 'c']);
    expect(jsonHttpClient.requestedObjectNames).toEqual([
      'usage/a.json',
      'usage/b.json',
      'usage/c.json',
    ]);
  });

  it.each([
    [
      'a self-loop',
      [
        ['', 'loop'],
        ['loop', 'loop'],
      ],
      ['', 'loop'],
    ],
    [
      'a multi-token cycle',
      [
        ['', 'first'],
        ['first', 'second'],
        ['second', 'third'],
        ['third', 'first'],
      ],
      ['', 'first', 'second', 'third'],
    ],
  ])(
    'rejects %s before requesting a repeated page token',
    async (_description, nextPageTokenByPageToken, expectedRequestedPageTokens) => {
      const { service, jsonHttpClient } = buildServiceWithFakeStorage(
        new Map(
          nextPageTokenByPageToken.map(([pageToken, nextPageToken]) => [
            pageToken,
            okResponse({ items: [{ name: `${pageToken}.json` }], nextPageToken }),
          ]),
        ),
      );

      await expect(service.fetchAllSnapshots()).rejects.toThrow(
        'snapshot listing pagination cycle',
      );
      expect(jsonHttpClient.requestedPageTokens).toEqual(expectedRequestedPageTokens);
      expect(jsonHttpClient.requestedObjectNames).toEqual([]);
    },
  );

  it('fetches reserved-character object names through the JSON API media endpoint', async () => {
    const objectNamesWithEncodedPaths = [
      ['snapshots/space name.json', 'snapshots%2Fspace%20name.json'],
      ['snapshots/ünï-日本.json', 'snapshots%2F%C3%BCn%C3%AF-%E6%97%A5%E6%9C%AC.json'],
      ['snapshots/nested/slash.json', 'snapshots%2Fnested%2Fslash.json'],
      ['snapshots/100%.json', 'snapshots%2F100%25.json'],
      ['snapshots/question?.json', 'snapshots%2Fquestion%3F.json'],
      ['snapshots/fragment#1.json', 'snapshots%2Ffragment%231.json'],
    ];
    const objectNames = objectNamesWithEncodedPaths.map(([objectName]) => objectName);
    const { service, jsonHttpClient } = buildServiceWithFakeStorage(
      singlePageListing(objectNames),
      new Map(objectNames.map((name) => [name, okResponse({ account_label: name })])),
    );

    const snapshots = await service.fetchAllSnapshots();

    expect(snapshots.map((snapshot) => snapshot.account_label)).toEqual(objectNames);
    expect(jsonHttpClient.requestedUrls.slice(1)).toEqual(
      objectNamesWithEncodedPaths.map(
        ([, encodedPath]) => `${objectMediaUrlPrefix}${encodedPath}?alt=media`,
      ),
    );
  });
});
