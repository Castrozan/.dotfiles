import type { JsonHttpResponse } from '../../dependencies/json-http-client/json-http-client.port';
import {
  ControlledSnapshotDownloadClient,
  okResponse,
  provideUsageSnapshotClient,
} from './cloud-storage-json-http-client.doubles';

const workloadObjectCount = 250;
const maximumDownloadsInFlight = 6;

function workloadObjectName(objectIndex: number): string {
  return `snapshots/account-${String(objectIndex).padStart(3, '0')}.json`;
}

function workloadOutcome(objectIndex: number): JsonHttpResponse | Error {
  if (objectIndex % 10 === 3) {
    return { ok: false, status: 503, body: null };
  }
  if (objectIndex % 10 === 7) {
    return new TypeError('Failed to fetch');
  }
  if (objectIndex % 25 === 11) {
    return okResponse({ account_label: 7 });
  }
  return okResponse({ account_label: workloadObjectName(objectIndex) });
}

function isValidWorkloadSnapshot(objectIndex: number): boolean {
  return objectIndex % 10 !== 3 && objectIndex % 10 !== 7 && objectIndex % 25 !== 11;
}

function flushAsyncWork(): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, 0));
}

describe('UsageSnapshotClientService download concurrency', () => {
  it('keeps six downloads in flight over 250 objects and refills each freed slot at once', async () => {
    const objectNames = Array.from({ length: workloadObjectCount }, (_unused, objectIndex) =>
      workloadObjectName(objectIndex),
    );
    const jsonHttpClient = new ControlledSnapshotDownloadClient({
      items: objectNames.map((name) => ({ name })),
    });
    const service = provideUsageSnapshotClient(jsonHttpClient);

    const snapshotsPromise = service.fetchAllSnapshots();
    await flushAsyncWork();
    expect(jsonHttpClient.startedObjectNames).toHaveLength(maximumDownloadsInFlight);
    expect(jsonHttpClient.pendingDownloadsByObjectName.size).toBe(maximumDownloadsInFlight);

    for (let settledCount = 1; settledCount <= workloadObjectCount; settledCount++) {
      const objectName = jsonHttpClient.mostRecentlyStartedPendingObjectName();
      jsonHttpClient.settle(objectName, workloadOutcome(objectNames.indexOf(objectName)));
      await flushAsyncWork();
      expect(jsonHttpClient.startedObjectNames).toHaveLength(
        Math.min(workloadObjectCount, settledCount + maximumDownloadsInFlight),
      );
      expect(jsonHttpClient.pendingDownloadsByObjectName.size).toBe(
        Math.min(maximumDownloadsInFlight, workloadObjectCount - settledCount),
      );
    }

    const expectedSnapshots = objectNames
      .filter((_objectName, objectIndex) => isValidWorkloadSnapshot(objectIndex))
      .map((objectName) => ({ account_label: objectName }));
    await expect(snapshotsPromise).resolves.toEqual(expectedSnapshots);
    expect(jsonHttpClient.highestInFlightCount).toBe(maximumDownloadsInFlight);
    expect([...jsonHttpClient.startedObjectNames].sort()).toEqual(objectNames);
  });
});
