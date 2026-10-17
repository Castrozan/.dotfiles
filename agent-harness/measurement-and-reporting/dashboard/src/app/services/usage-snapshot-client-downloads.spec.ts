import { TestBed } from '@angular/core/testing';
import {
  JSON_HTTP_CLIENT,
  type JsonHttpResponse,
} from '../dependencies/json-http-client/json-http-client.port';
import {
  ControlledJsonHttpClient,
  okResponse,
  settleMicrotasks,
  type PendingSnapshotRequest,
} from './testing/controlled-json-http-client';
import { UsageSnapshotClientService } from './usage-snapshot-client.service';

function snapshotMediaUrl(objectName: string): string {
  return `https://storage.googleapis.com/storage/v1/b/zg-url-shortener-2026-dotfiles-usage-snapshots/o/${encodeURIComponent(objectName)}?alt=media`;
}

function buildControlledService(listingPagesByToken: Map<string | null, JsonHttpResponse>) {
  const jsonHttpClient = new ControlledJsonHttpClient(listingPagesByToken);
  TestBed.configureTestingModule({
    providers: [{ provide: JSON_HTTP_CLIENT, useValue: jsonHttpClient }],
  });
  return { service: TestBed.inject(UsageSnapshotClientService), jsonHttpClient };
}

function objectNameForIndex(objectIndex: number): string {
  return `snapshots/object-${String(objectIndex).padStart(3, '0')}.json`;
}

function respondToSnapshotRequest(request: PendingSnapshotRequest, objectIndex: number): void {
  if (objectIndex % 10 === 3) {
    request.respond({ ok: false, status: 404, body: null });
  } else if (objectIndex % 10 === 7) {
    request.respond(okResponse({ account_label: objectIndex }));
  } else if (objectIndex % 25 === 11) {
    request.fail(new TypeError('network unavailable'));
  } else {
    request.respond(okResponse({ account_label: `account-${objectIndex}` }));
  }
}

function isRetainedObjectIndex(objectIndex: number): boolean {
  return objectIndex % 10 !== 3 && objectIndex % 10 !== 7 && objectIndex % 25 !== 11;
}

describe('UsageSnapshotClientService snapshot downloads', () => {
  it('downloads a 250-object workload six at a time, refilling each settled slot immediately', async () => {
    const objectIndexes = Array.from({ length: 250 }, (_unused, objectIndex) => objectIndex);
    const firstPageNames = objectIndexes.slice(0, 120).map(objectNameForIndex);
    const secondPageNames = [
      ...objectIndexes.slice(100, 200).map(objectNameForIndex),
      'snapshots/readme.txt',
    ];
    const thirdPageNames = [
      ...objectIndexes.slice(190, 250).map(objectNameForIndex),
      objectNameForIndex(0),
    ];
    const { service, jsonHttpClient } = buildControlledService(
      new Map<string | null, JsonHttpResponse>([
        [
          null,
          okResponse({ items: firstPageNames.map((name) => ({ name })), nextPageToken: 'p2' }),
        ],
        [
          'p2',
          okResponse({ items: secondPageNames.map((name) => ({ name })), nextPageToken: 'p3' }),
        ],
        ['p3', okResponse({ items: thirdPageNames.map((name) => ({ name })) })],
      ]),
    );
    const objectIndexByUrl = new Map(
      objectIndexes.map((objectIndex) => [
        snapshotMediaUrl(objectNameForIndex(objectIndex)),
        objectIndex,
      ]),
    );

    const loadedSnapshots = service.fetchAllSnapshots();
    await settleMicrotasks();

    let settledRequestCount = 0;
    while (jsonHttpClient.pendingSnapshotRequests.length > 0) {
      expect(jsonHttpClient.activeSnapshotRequestCount).toBe(
        Math.min(6, 250 - settledRequestCount),
      );
      const pendingRequests = jsonHttpClient.pendingSnapshotRequests;
      const settlingRequest = pendingRequests[(settledRequestCount * 5) % pendingRequests.length];
      const startedBeforeSettling = jsonHttpClient.requestedSnapshotUrls.length;
      const objectIndex = objectIndexByUrl.get(settlingRequest.url);
      expect(objectIndex).toBeDefined();
      respondToSnapshotRequest(settlingRequest, objectIndex ?? -1);
      settledRequestCount += 1;
      await settleMicrotasks();
      expect(jsonHttpClient.requestedSnapshotUrls.length).toBe(
        Math.min(250, startedBeforeSettling + 1),
      );
    }

    const expectedLabels = objectIndexes
      .filter(isRetainedObjectIndex)
      .map((objectIndex) => `account-${objectIndex}`);
    await expect(loadedSnapshots).resolves.toEqual(
      expectedLabels.map((accountLabel) => ({ account_label: accountLabel })),
    );
    expect(settledRequestCount).toBe(250);
    expect(jsonHttpClient.peakSnapshotRequestCount).toBe(6);
    expect(jsonHttpClient.requestedSnapshotUrls).toEqual(
      objectIndexes.map((objectIndex) => snapshotMediaUrl(objectNameForIndex(objectIndex))),
    );
    expect(jsonHttpClient.requestedPageTokens).toEqual([null, 'p2', 'p3']);
  });

  it('starts every download of a short listing at once', async () => {
    const { service, jsonHttpClient } = buildControlledService(
      new Map<string | null, JsonHttpResponse>([
        [null, okResponse({ items: [{ name: 'a.json' }, { name: 'b.json' }, { name: 'a.json' }] })],
      ]),
    );

    const loadedSnapshots = service.fetchAllSnapshots();
    await settleMicrotasks();

    expect(jsonHttpClient.requestedSnapshotUrls).toEqual([
      snapshotMediaUrl('a.json'),
      snapshotMediaUrl('b.json'),
    ]);
    const [firstRequest, secondRequest] = jsonHttpClient.pendingSnapshotRequests;
    secondRequest.respond(okResponse({ account_label: 'b' }));
    firstRequest.respond(okResponse({ account_label: 'a' }));
    await expect(loadedSnapshots).resolves.toEqual([
      { account_label: 'a' },
      { account_label: 'b' },
    ]);
  });

  it('fully encodes reserved and Unicode characters in snapshot object names', async () => {
    const objectNames = [
      'snapshots/with space.json',
      'snapshots/ünïcödé-日本.json',
      'snapshots/nested/path.json',
      'snapshots/100%25 done.json',
      'snapshots/question?.json',
      'snapshots/fragment#part.json',
      'snapshots/plus+and&equals=.json',
    ];
    const { service, jsonHttpClient } = buildControlledService(
      new Map<string | null, JsonHttpResponse>([
        [null, okResponse({ items: objectNames.map((name) => ({ name })) })],
      ]),
    );

    const loadedSnapshots = service.fetchAllSnapshots();
    await settleMicrotasks();
    while (jsonHttpClient.pendingSnapshotRequests.length > 0) {
      jsonHttpClient.pendingSnapshotRequests[0].respond(okResponse({}));
      await settleMicrotasks();
    }
    await expect(loadedSnapshots).resolves.toHaveLength(objectNames.length);

    expect(jsonHttpClient.requestedSnapshotUrls).toEqual([
      'https://storage.googleapis.com/storage/v1/b/zg-url-shortener-2026-dotfiles-usage-snapshots/o/snapshots%2Fwith%20space.json?alt=media',
      'https://storage.googleapis.com/storage/v1/b/zg-url-shortener-2026-dotfiles-usage-snapshots/o/snapshots%2F%C3%BCn%C3%AFc%C3%B6d%C3%A9-%E6%97%A5%E6%9C%AC.json?alt=media',
      'https://storage.googleapis.com/storage/v1/b/zg-url-shortener-2026-dotfiles-usage-snapshots/o/snapshots%2Fnested%2Fpath.json?alt=media',
      'https://storage.googleapis.com/storage/v1/b/zg-url-shortener-2026-dotfiles-usage-snapshots/o/snapshots%2F100%2525%20done.json?alt=media',
      'https://storage.googleapis.com/storage/v1/b/zg-url-shortener-2026-dotfiles-usage-snapshots/o/snapshots%2Fquestion%3F.json?alt=media',
      'https://storage.googleapis.com/storage/v1/b/zg-url-shortener-2026-dotfiles-usage-snapshots/o/snapshots%2Ffragment%23part.json?alt=media',
      'https://storage.googleapis.com/storage/v1/b/zg-url-shortener-2026-dotfiles-usage-snapshots/o/snapshots%2Fplus%2Band%26equals%3D.json?alt=media',
    ]);
  });
});
