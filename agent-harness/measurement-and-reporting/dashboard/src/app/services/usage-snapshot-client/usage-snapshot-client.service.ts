import { Injectable, inject } from '@angular/core';
import {
  DASHBOARD_CONFIGURATION,
  type DashboardConfiguration,
} from '../../config/dashboard-config';
import { JSON_HTTP_CLIENT } from '../../dependencies/json-http-client/json-http-client.port';
import type { UsageSnapshot } from '../../models/usage-snapshot.model';
import {
  type StorageObjectListing,
  parseStorageObjectListing,
} from '../../models/storage-object-listing-parser';
import { parseUsageSnapshot } from '../../models/usage-snapshot-parser';

const MAXIMUM_CONCURRENT_SNAPSHOT_DOWNLOADS = 6;

function encodeObjectNameSegment(objectName: string): string {
  return encodeURIComponent(objectName).replace(
    /[!'()*]/g,
    (character) => `%${character.charCodeAt(0).toString(16).toUpperCase()}`,
  );
}

function addSnapshotObjectNames(objectNames: Set<string>, listing: StorageObjectListing): void {
  for (const item of listing.items ?? []) {
    if (item.name.endsWith('.json')) {
      objectNames.add(item.name);
    }
  }
}

function takeUnrequestedPageToken(
  requestedPageTokens: Set<string>,
  nextPageToken: string | undefined,
): string | undefined {
  if (!nextPageToken) {
    return undefined;
  }
  if (requestedPageTokens.has(nextPageToken)) {
    throw new Error(
      `snapshot listing pagination cycle: page token "${nextPageToken}" was already requested`,
    );
  }
  requestedPageTokens.add(nextPageToken);
  return nextPageToken;
}

@Injectable({ providedIn: 'root' })
export class UsageSnapshotClientService {
  private readonly configuration: DashboardConfiguration = DASHBOARD_CONFIGURATION;
  private readonly jsonHttpClient = inject(JSON_HTTP_CLIENT);
  private readonly objectsCollectionUrl = `https://storage.googleapis.com/storage/v1/b/${this.configuration.snapshotsBucket}/o`;

  async fetchAllSnapshots(): Promise<UsageSnapshot[]> {
    const objectNames = await this.listSnapshotObjectNames();
    const snapshots = await this.fetchSnapshotObjectsInListingOrder(objectNames);
    return snapshots.filter((snapshot): snapshot is UsageSnapshot => snapshot !== null);
  }

  private async fetchSnapshotObjectsInListingOrder(
    objectNames: readonly string[],
  ): Promise<(UsageSnapshot | null)[]> {
    const snapshots: (UsageSnapshot | null)[] = [];
    let nextObjectIndex = 0;
    const fetchUntilListingIsExhausted = async (): Promise<void> => {
      while (nextObjectIndex < objectNames.length) {
        const objectIndex = nextObjectIndex++;
        snapshots[objectIndex] = await this.fetchSnapshotObject(objectNames[objectIndex]);
      }
    };
    const workerCount = Math.min(MAXIMUM_CONCURRENT_SNAPSHOT_DOWNLOADS, objectNames.length);
    await Promise.all(Array.from({ length: workerCount }, fetchUntilListingIsExhausted));
    return snapshots;
  }

  private async listSnapshotObjectNames(): Promise<string[]> {
    const objectNames = new Set<string>();
    const requestedPageTokens = new Set<string>();
    let pageToken: string | undefined;
    do {
      const listing = await this.fetchObjectListingPage(pageToken);
      addSnapshotObjectNames(objectNames, listing);
      pageToken = takeUnrequestedPageToken(requestedPageTokens, listing.nextPageToken);
    } while (pageToken);
    return [...objectNames];
  }

  private buildObjectListingUrl(pageToken: string | undefined): string {
    const listUrl = new URL(this.objectsCollectionUrl);
    listUrl.searchParams.set('prefix', this.configuration.snapshotsObjectPrefix);
    listUrl.searchParams.set('fields', 'items(name),nextPageToken');
    if (pageToken) {
      listUrl.searchParams.set('pageToken', pageToken);
    }
    return listUrl.toString();
  }

  private async fetchObjectListingPage(
    pageToken: string | undefined,
  ): Promise<StorageObjectListing> {
    const response = await this.jsonHttpClient.getJson(this.buildObjectListingUrl(pageToken));
    if (!response.ok) {
      throw new Error(`snapshot listing failed with status ${response.status}`);
    }
    return parseStorageObjectListing(response.body);
  }

  private buildSnapshotObjectMediaUrl(objectName: string): string {
    return `${this.objectsCollectionUrl}/${encodeObjectNameSegment(objectName)}?alt=media`;
  }

  private async fetchSnapshotObject(objectName: string): Promise<UsageSnapshot | null> {
    try {
      const response = await this.jsonHttpClient.getJson(
        this.buildSnapshotObjectMediaUrl(objectName),
      );
      return response.ok ? parseUsageSnapshot(response.body) : null;
    } catch {
      return null;
    }
  }
}
