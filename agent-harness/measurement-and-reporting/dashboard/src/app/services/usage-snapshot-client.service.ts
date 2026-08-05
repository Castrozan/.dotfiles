import { Injectable, inject } from '@angular/core';
import { DASHBOARD_CONFIGURATION, DashboardConfiguration } from '../config/dashboard-config';
import { JSON_HTTP_CLIENT } from '../dependencies/json-http-client/json-http-client.port';
import { UsageSnapshot } from '../models/usage-snapshot.model';

interface StorageObjectListing {
  items?: { name: string }[];
  nextPageToken?: string;
}

@Injectable({ providedIn: 'root' })
export class UsageSnapshotClientService {
  private readonly configuration: DashboardConfiguration = DASHBOARD_CONFIGURATION;
  private readonly jsonHttpClient = inject(JSON_HTTP_CLIENT);

  async fetchAllSnapshots(): Promise<UsageSnapshot[]> {
    const objectNames = await this.listSnapshotObjectNames();
    const snapshots = await Promise.all(
      objectNames.map((objectName) => this.fetchSnapshotObject(objectName)),
    );
    return snapshots.filter((snapshot): snapshot is UsageSnapshot => snapshot !== null);
  }

  private async listSnapshotObjectNames(): Promise<string[]> {
    const objectNames: string[] = [];
    let pageToken: string | undefined;
    do {
      const listing = await this.fetchObjectListingPage(pageToken);
      for (const item of listing.items ?? []) {
        if (item.name.endsWith('.json')) {
          objectNames.push(item.name);
        }
      }
      pageToken = listing.nextPageToken;
    } while (pageToken);
    return objectNames;
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
    const response = await this.jsonHttpClient.getJson<StorageObjectListing>(
      this.buildObjectListingUrl(pageToken),
    );
    if (!response.ok || response.body === null) {
      throw new Error(`snapshot listing failed with status ${response.status}`);
    }
    return response.body;
  }

  private async fetchSnapshotObject(objectName: string): Promise<UsageSnapshot | null> {
    const mediaUrl = `https://storage.googleapis.com/${this.configuration.snapshotsBucket}/${objectName}`;
    try {
      const response = await this.jsonHttpClient.getJson<UsageSnapshot>(mediaUrl);
      return response.ok ? response.body : null;
    } catch {
      return null;
    }
  }
}
