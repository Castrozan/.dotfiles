import { Injectable, inject } from '@angular/core';
import { DASHBOARD_CONFIGURATION, DashboardConfiguration } from '../config/dashboard-config';
import { JSON_HTTP_CLIENT } from '../dependencies/json-http-client/json-http-client.port';
import type { UsageSnapshot } from '../models/usage-snapshot.model';
import {
  type StorageObjectListing,
  parseStorageObjectListing,
} from '../models/storage-object-listing-parser';
import { parseUsageSnapshot } from '../models/usage-snapshot-parser';
import {
  buildObjectListingUrl,
  buildObjectMediaUrl,
} from './usage-snapshot-client/cloud-storage-object-urls';

const maximumSnapshotDownloadsInFlight = 6;

function addSnapshotObjectNames(objectNames: Set<string>, listing: StorageObjectListing): void {
  for (const item of listing.items ?? []) {
    if (item.name.endsWith('.json')) {
      objectNames.add(item.name);
    }
  }
}

function claimNextPageToken(
  requestedPageTokens: Set<string>,
  nextPageToken: string | undefined,
): string | undefined {
  if (!nextPageToken) {
    return undefined;
  }
  if (requestedPageTokens.has(nextPageToken)) {
    throw new Error(`snapshot listing pagination cycle at page token ${nextPageToken}`);
  }
  requestedPageTokens.add(nextPageToken);
  return nextPageToken;
}

@Injectable({ providedIn: 'root' })
export class UsageSnapshotClientService {
  private readonly configuration: DashboardConfiguration = DASHBOARD_CONFIGURATION;
  private readonly jsonHttpClient = inject(JSON_HTTP_CLIENT);

  async fetchAllSnapshots(): Promise<UsageSnapshot[]> {
    const objectNames = await this.listSnapshotObjectNames();
    const snapshots = await this.downloadSnapshotsInListingOrder(objectNames);
    return snapshots.filter((snapshot): snapshot is UsageSnapshot => snapshot !== null);
  }

  private async downloadSnapshotsInListingOrder(
    objectNames: string[],
  ): Promise<(UsageSnapshot | null)[]> {
    const snapshots = new Array<UsageSnapshot | null>(objectNames.length).fill(null);
    let nextObjectIndex = 0;
    const runDownloadSlot = async (): Promise<void> => {
      while (nextObjectIndex < objectNames.length) {
        const objectIndex = nextObjectIndex++;
        snapshots[objectIndex] = await this.fetchSnapshotObject(objectNames[objectIndex]);
      }
    };
    const downloadSlotCount = Math.min(maximumSnapshotDownloadsInFlight, objectNames.length);
    await Promise.all(Array.from({ length: downloadSlotCount }, runDownloadSlot));
    return snapshots;
  }

  private async listSnapshotObjectNames(): Promise<string[]> {
    const objectNames = new Set<string>();
    const requestedPageTokens = new Set<string>();
    let pageToken: string | undefined;
    do {
      const listing = await this.fetchObjectListingPage(pageToken);
      addSnapshotObjectNames(objectNames, listing);
      pageToken = claimNextPageToken(requestedPageTokens, listing.nextPageToken);
    } while (pageToken);
    return [...objectNames];
  }

  private async fetchObjectListingPage(
    pageToken: string | undefined,
  ): Promise<StorageObjectListing> {
    const response = await this.jsonHttpClient.getJson(
      buildObjectListingUrl(
        this.configuration.snapshotsBucket,
        this.configuration.snapshotsObjectPrefix,
        pageToken,
      ),
    );
    if (!response.ok) {
      throw new Error(`snapshot listing failed with status ${response.status}`);
    }
    return parseStorageObjectListing(response.body);
  }

  private async fetchSnapshotObject(objectName: string): Promise<UsageSnapshot | null> {
    try {
      const response = await this.jsonHttpClient.getJson(
        buildObjectMediaUrl(this.configuration.snapshotsBucket, objectName),
      );
      return response.ok ? parseUsageSnapshot(response.body) : null;
    } catch {
      return null;
    }
  }
}
