import { TestBed } from '@angular/core/testing';
import { DASHBOARD_CONFIGURATION } from '../../config/dashboard-config';
import {
  JSON_HTTP_CLIENT,
  type JsonHttpClientPort,
  type JsonHttpResponse,
} from '../../dependencies/json-http-client/json-http-client.port';
import { UsageSnapshotClientService } from '../usage-snapshot-client.service';

export const objectCollectionPath = `/storage/v1/b/${DASHBOARD_CONFIGURATION.snapshotsBucket}/o`;
const listingRequestLimit = 20;
const notFoundResponse: JsonHttpResponse = { ok: false, status: 404, body: null };

export function okResponse(body: unknown): JsonHttpResponse {
  return { ok: true, status: 200, body };
}

function objectNameFromMediaUrl(url: URL): string {
  if (
    url.searchParams.get('alt') !== 'media' ||
    !url.pathname.startsWith(`${objectCollectionPath}/`)
  ) {
    throw new Error(`Unexpected snapshot request ${url.href}`);
  }
  return decodeURIComponent(url.pathname.slice(objectCollectionPath.length + 1));
}

export class FakeCloudStorageJsonHttpClient implements JsonHttpClientPort {
  readonly requestedUrls: string[] = [];
  readonly requestedPageTokens: string[] = [];
  readonly requestedObjectNames: string[] = [];

  constructor(
    private readonly listingResponsesByPageToken: Map<string, JsonHttpResponse>,
    private readonly objectResponsesByName: Map<string, JsonHttpResponse>,
  ) {}

  async getJson(url: string): Promise<JsonHttpResponse> {
    this.requestedUrls.push(url);
    const parsedUrl = new URL(url);
    if (parsedUrl.pathname === objectCollectionPath) {
      return this.respondToListing(parsedUrl.searchParams.get('pageToken') ?? '');
    }
    const objectName = objectNameFromMediaUrl(parsedUrl);
    this.requestedObjectNames.push(objectName);
    return this.objectResponsesByName.get(objectName) ?? notFoundResponse;
  }

  private respondToListing(pageToken: string): JsonHttpResponse {
    if (this.requestedPageTokens.length >= listingRequestLimit) {
      throw new Error('Listing request limit exceeded');
    }
    this.requestedPageTokens.push(pageToken);
    return this.listingResponsesByPageToken.get(pageToken) ?? notFoundResponse;
  }
}

interface PendingSnapshotDownload {
  resolve(response: JsonHttpResponse): void;
  reject(error: Error): void;
}

export class ControlledSnapshotDownloadClient implements JsonHttpClientPort {
  readonly startedObjectNames: string[] = [];
  readonly pendingDownloadsByObjectName = new Map<string, PendingSnapshotDownload>();
  highestInFlightCount = 0;

  constructor(private readonly listingBody: unknown) {}

  getJson(url: string): Promise<JsonHttpResponse> {
    const parsedUrl = new URL(url);
    if (parsedUrl.pathname === objectCollectionPath) {
      return Promise.resolve(okResponse(this.listingBody));
    }
    const objectName = objectNameFromMediaUrl(parsedUrl);
    this.startedObjectNames.push(objectName);
    return new Promise((resolve, reject) => {
      this.pendingDownloadsByObjectName.set(objectName, { resolve, reject });
      this.highestInFlightCount = Math.max(
        this.highestInFlightCount,
        this.pendingDownloadsByObjectName.size,
      );
    });
  }

  mostRecentlyStartedPendingObjectName(): string {
    const objectName = [...this.pendingDownloadsByObjectName.keys()].at(-1);
    if (objectName === undefined) {
      throw new Error('No snapshot download is pending');
    }
    return objectName;
  }

  settle(objectName: string, outcome: JsonHttpResponse | Error): void {
    const pendingDownload = this.pendingDownloadsByObjectName.get(objectName);
    if (pendingDownload === undefined) {
      throw new Error(`No pending download for ${objectName}`);
    }
    this.pendingDownloadsByObjectName.delete(objectName);
    if (outcome instanceof Error) {
      pendingDownload.reject(outcome);
    } else {
      pendingDownload.resolve(outcome);
    }
  }
}

export function provideUsageSnapshotClient(
  jsonHttpClient: JsonHttpClientPort,
): UsageSnapshotClientService {
  TestBed.configureTestingModule({
    providers: [{ provide: JSON_HTTP_CLIENT, useValue: jsonHttpClient }],
  });
  return TestBed.inject(UsageSnapshotClientService);
}

export function buildServiceWithFakeStorage(
  listingResponsesByPageToken: Map<string, JsonHttpResponse>,
  objectResponsesByName = new Map<string, JsonHttpResponse>(),
) {
  const jsonHttpClient = new FakeCloudStorageJsonHttpClient(
    listingResponsesByPageToken,
    objectResponsesByName,
  );
  return { service: provideUsageSnapshotClient(jsonHttpClient), jsonHttpClient };
}

export function singlePageListing(objectNames: string[]): Map<string, JsonHttpResponse> {
  return new Map([['', okResponse({ items: objectNames.map((name) => ({ name })) })]]);
}
