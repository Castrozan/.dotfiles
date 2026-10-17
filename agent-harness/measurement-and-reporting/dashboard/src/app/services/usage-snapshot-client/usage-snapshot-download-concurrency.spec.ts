import {
  ControlledSnapshotStorage,
  FIRST_LISTING_PAGE,
  type SnapshotDownloadOutcome,
  buildSnapshotClientService,
  flushAsyncWork,
  listingOf,
  okResponse,
} from './storage-json-http-client-doubles';

const MAXIMUM_CONCURRENT_DOWNLOADS = 6;
const OBJECT_NAMES = Array.from(
  { length: 250 },
  (_value, index) => `snapshots/machine-${String(index).padStart(3, '0')}.json`,
);
const OBJECT_INDEX_BY_NAME = new Map(OBJECT_NAMES.map((name, index) => [name, index]));
const UNAVAILABLE_REMAINDER = 3;
const MALFORMED_REMAINDER = 5;
const REJECTED_REMAINDER = 7;
const SKIPPED_REMAINDERS = [UNAVAILABLE_REMAINDER, MALFORMED_REMAINDER, REJECTED_REMAINDER];
const VALID_OBJECT_NAMES = OBJECT_NAMES.filter(
  (_name, index) => !SKIPPED_REMAINDERS.includes(index % 10),
);

function outcomeFor(objectName: string): SnapshotDownloadOutcome {
  switch ((OBJECT_INDEX_BY_NAME.get(objectName) ?? 0) % 10) {
    case UNAVAILABLE_REMAINDER:
      return { response: { ok: false, status: 503, body: null } };
    case MALFORMED_REMAINDER:
      return { response: okResponse({ account_label: 7 }) };
    case REJECTED_REMAINDER:
      return { failure: new TypeError('Failed to fetch') };
    default:
      return { response: okResponse({ account_label: objectName }) };
  }
}

function buildControlledStorage() {
  return new ControlledSnapshotStorage(
    new Map<string, unknown>([
      [
        FIRST_LISTING_PAGE,
        {
          ...listingOf(...OBJECT_NAMES.slice(0, 100), 'snapshots/readme.txt'),
          nextPageToken: 'second',
        },
      ],
      [
        'second',
        {
          ...listingOf(OBJECT_NAMES[4], ...OBJECT_NAMES.slice(100, 200), OBJECT_NAMES[99]),
          nextPageToken: 'third',
        },
      ],
      ['third', listingOf(...OBJECT_NAMES.slice(200), OBJECT_NAMES[0], OBJECT_NAMES[150])],
    ]),
  );
}

describe('UsageSnapshotClientService with a controlled 250-object workload', () => {
  it('keeps six downloads in flight, refills each settled slot at once and preserves order', async () => {
    const storage = buildControlledStorage();
    const service = buildSnapshotClientService(storage);

    const loading = service.fetchAllSnapshots();
    await flushAsyncWork();

    expect(storage.pendingDownloads).toHaveLength(MAXIMUM_CONCURRENT_DOWNLOADS);
    let settledCount = 0;
    while (storage.pendingDownloads.length > 0) {
      const startedBeforeSettling = storage.startedObjectNames.length;
      const settlingPosition = (settledCount * 7) % storage.pendingDownloads.length;
      storage.settlePendingDownloadAt(settlingPosition, outcomeFor);
      settledCount += 1;
      await flushAsyncWork();

      const unstartedCount = OBJECT_NAMES.length - startedBeforeSettling;
      expect(storage.startedObjectNames).toHaveLength(
        startedBeforeSettling + Math.min(1, unstartedCount),
      );
      expect(storage.pendingDownloads).toHaveLength(
        Math.min(MAXIMUM_CONCURRENT_DOWNLOADS, OBJECT_NAMES.length - settledCount),
      );
    }
    const snapshots = await loading;

    expect(settledCount).toBe(OBJECT_NAMES.length);
    expect(storage.maximumInFlightCount).toBe(MAXIMUM_CONCURRENT_DOWNLOADS);
    expect(storage.startedObjectNames).toEqual(OBJECT_NAMES);
    expect(snapshots.map((snapshot) => snapshot.account_label)).toEqual(VALID_OBJECT_NAMES);
  });

  it('returns listing order when the newest download always settles first', async () => {
    const storage = buildControlledStorage();
    const service = buildSnapshotClientService(storage);

    const loading = service.fetchAllSnapshots();
    await flushAsyncWork();
    while (storage.pendingDownloads.length > 0) {
      storage.settlePendingDownloadAt(storage.pendingDownloads.length - 1, outcomeFor);
      await flushAsyncWork();
    }
    const snapshots = await loading;

    expect(storage.maximumInFlightCount).toBe(MAXIMUM_CONCURRENT_DOWNLOADS);
    expect(snapshots.map((snapshot) => snapshot.account_label)).toEqual(VALID_OBJECT_NAMES);
  });
});
