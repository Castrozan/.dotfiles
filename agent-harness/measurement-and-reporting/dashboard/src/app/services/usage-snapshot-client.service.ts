import { Injectable, inject } from '@angular/core';
import { DASHBOARD_CONFIGURATION, DashboardConfiguration } from '../config/dashboard-config';
import { JSON_HTTP_CLIENT } from '../dependencies/json-http-client/json-http-client.port';
import type { UsageSnapshot } from '../models/usage-snapshot.model';
import {
  type StorageObjectListing,
  parseStorageObjectListing,
} from '../models/storage-object-listing-parser';
import { parseUsageSnapshot } from '../models/usage-snapshot-parser';

const MAXIMUM_CONCURRENT_SNAPSHOT_DOWNLOADS = 6;

function collectSnapshotObjectNames(listing: StorageObjectListing, objectNames: Set<string>): void {
  for (const item of listing.items ?? []) {
    if (item.name.endsWith('.json')) {
      objectNames.add(item.name);
    }
  }
}

function recordUnrequestedPageToken(requestedPageTokens: Set<string>, pageToken: string): void {
  if (requestedPageTokens.has(pageToken)) {
    throw new Error(`snapshot listing pagination cycle repeats page token "${pageToken}"`);
  }
  requestedPageTokens.add(pageToken);
}

@Injectable({ providedIn: 'root' })
export class UsageSnapshotClientService {
  private readonly configuration: DashboardConfiguration = DASHBOARD_CONFIGURATION;
  private readonly jsonHttpClient = inject(JSON_HTTP_CLIENT);

  async fetchAllSnapshots(): Promise<UsageSnapshot[]> {
    const objectNames = await this.listSnapshotObjectNames();
    const snapshots = await this.downloadSnapshotObjects(objectNames);
    return snapshots.filter((snapshot): snapshot is UsageSnapshot => snapshot !== null);
  }

  private async listSnapshotObjectNames(): Promise<string[]> {
    const objectNames = new Set<string>();
    const requestedPageTokens = new Set<string>();
    let pageToken: string | undefined;
    do {
      const listing = await this.fetchObjectListingPage(pageToken);
      collectSnapshotObjectNames(listing, objectNames);
      pageToken = listing.nextPageToken;
      if (pageToken) {
        recordUnrequestedPageToken(requestedPageTokens, pageToken);
      }
    } while (pageToken);
    return [...objectNames];
  }

  private async downloadSnapshotObjects(
    objectNames: readonly string[],
  ): Promise<(UsageSnapshot | null)[]> {
    const snapshots: (UsageSnapshot | null)[] = objectNames.map(() => null);
    let nextObjectIndex = 0;
    const downloadRemainingSnapshotObjects = async (): Promise<void> => {
      while (nextObjectIndex < objectNames.length) {
        const objectIndex = nextObjectIndex;
        nextObjectIndex += 1;
        snapshots[objectIndex] = await this.fetchSnapshotObject(objectNames[objectIndex]);
      }
    };
    const downloadWorkerCount = Math.min(MAXIMUM_CONCURRENT_SNAPSHOT_DOWNLOADS, objectNames.length);
    await Promise.all(
      Array.from({ length: downloadWorkerCount }, () => downloadRemainingSnapshotObjects()),
    );
    return snapshots;
  }

  private buildObjectListingUrl(pageToken: string | undefined): string {
    const listUrl = new URL(
      `https://storage.googleapis.com/storage/v1/b/${this.configuration.snapshotsBucket}/o`,
    );
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

  private buildSnapshotMediaUrl(objectName: string): string {
    return `https://storage.googleapis.com/storage/v1/b/${this.configuration.snapshotsBucket}/o/${encodeURIComponent(objectName)}?alt=media`;
  }

  private async fetchSnapshotObject(objectName: string): Promise<UsageSnapshot | null> {
    try {
      const response = await this.jsonHttpClient.getJson(this.buildSnapshotMediaUrl(objectName));
      return response.ok ? parseUsageSnapshot(response.body) : null;
    } catch {
      return null;
    }
  }
}
