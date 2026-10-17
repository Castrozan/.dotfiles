import { TestBed } from '@angular/core/testing';
import { DASHBOARD_CONFIGURATION } from '../../config/dashboard-config';
import {
  JSON_HTTP_CLIENT,
  type JsonHttpClientPort,
  type JsonHttpResponse,
} from '../../dependencies/json-http-client/json-http-client.port';
import { UsageSnapshotClientService } from './usage-snapshot-client.service';

export const FIRST_LISTING_PAGE = '';

const OBJECTS_COLLECTION_URL = `https://storage.googleapis.com/storage/v1/b/${DASHBOARD_CONFIGURATION.snapshotsBucket}/o`;

type StorageRequest =
  { kind: 'listing'; pageToken: string } | { kind: 'object'; objectName: string };

function describeListingRequest(requestUrl: URL): StorageRequest {
  if (requestUrl.searchParams.get('prefix') !== DASHBOARD_CONFIGURATION.snapshotsObjectPrefix) {
    throw new Error(`Unexpected listing prefix in ${requestUrl}`);
  }
  const pageToken = requestUrl.searchParams.get('pageToken') ?? FIRST_LISTING_PAGE;
  return { kind: 'listing', pageToken };
}

function describeObjectMediaRequest(requestUrl: URL, requestPath: string): StorageRequest {
  const objectPathPrefix = `${OBJECTS_COLLECTION_URL}/`;
  const encodedObjectName = requestPath.slice(objectPathPrefix.length);
  const isSingleSegmentMediaRequest =
    requestPath.startsWith(objectPathPrefix) &&
    !encodedObjectName.includes('/') &&
    requestUrl.search === '?alt=media';
  if (!isSingleSegmentMediaRequest) {
    throw new Error(`Unexpected storage request ${requestUrl}`);
  }
  return { kind: 'object', objectName: decodeURIComponent(encodedObjectName) };
}

function describeStorageRequest(url: string): StorageRequest {
  const requestUrl = new URL(url);
  const requestPath = `${requestUrl.origin}${requestUrl.pathname}`;
  return requestPath === OBJECTS_COLLECTION_URL
    ? describeListingRequest(requestUrl)
    : describeObjectMediaRequest(requestUrl, requestPath);
}

export function okResponse(body: unknown): JsonHttpResponse {
  return { ok: true, status: 200, body };
}

export function listingOf(...objectNames: string[]) {
  return { items: objectNames.map((name) => ({ name })) };
}

export function singleListingPage(body: unknown): Map<string, JsonHttpResponse> {
  return new Map([[FIRST_LISTING_PAGE, okResponse(body)]]);
}

export class RecordingStorageJsonHttpClient implements JsonHttpClientPort {
  readonly requestedUrls: string[] = [];

  constructor(
    private readonly listingPagesByToken: Map<string, JsonHttpResponse>,
    private readonly objectResponsesByName: Map<string, JsonHttpResponse> = new Map(),
  ) {}

  async getJson(url: string): Promise<JsonHttpResponse> {
    const repeatsEarlierRequest = this.requestedUrls.includes(url);
    this.requestedUrls.push(url);
    if (repeatsEarlierRequest) {
      throw new Error('Unexpected repeated HTTP request');
    }
    const request = describeStorageRequest(url);
    const response =
      request.kind === 'listing'
        ? this.listingPagesByToken.get(request.pageToken)
        : this.objectResponsesByName.get(request.objectName);
    return response ?? { ok: false, status: 404, body: null };
  }

  requestedObjectNames(): string[] {
    return this.requestedUrls
      .map(describeStorageRequest)
      .flatMap((request) => (request.kind === 'object' ? [request.objectName] : []));
  }
}

export type SnapshotDownloadOutcome = { response: JsonHttpResponse } | { failure: Error };

interface PendingSnapshotDownload {
  objectName: string;
  settle(outcome: SnapshotDownloadOutcome): void;
}

export class ControlledSnapshotStorage implements JsonHttpClientPort {
  readonly startedObjectNames: string[] = [];
  readonly pendingDownloads: PendingSnapshotDownload[] = [];
  maximumInFlightCount = 0;

  constructor(private readonly listingPagesByToken: Map<string, unknown>) {}

  async getJson(url: string): Promise<JsonHttpResponse> {
    const request = describeStorageRequest(url);
    if (request.kind === 'listing') {
      return okResponse(this.listingPagesByToken.get(request.pageToken));
    }
    this.startedObjectNames.push(request.objectName);
    return new Promise<JsonHttpResponse>((resolve, reject) => {
      this.pendingDownloads.push({
        objectName: request.objectName,
        settle: (outcome) =>
          'response' in outcome ? resolve(outcome.response) : reject(outcome.failure),
      });
      this.maximumInFlightCount = Math.max(this.maximumInFlightCount, this.pendingDownloads.length);
    });
  }

  settlePendingDownloadAt(
    position: number,
    outcomeFor: (objectName: string) => SnapshotDownloadOutcome,
  ): void {
    const [download] = this.pendingDownloads.splice(position, 1);
    download.settle(outcomeFor(download.objectName));
  }
}

export function flushAsyncWork(): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, 0));
}

export function buildSnapshotClientService(jsonHttpClient: JsonHttpClientPort) {
  TestBed.configureTestingModule({
    providers: [{ provide: JSON_HTTP_CLIENT, useValue: jsonHttpClient }],
  });
  return TestBed.inject(UsageSnapshotClientService);
}

export function buildRecordingSnapshotClientService(
  listingPagesByToken: Map<string, JsonHttpResponse>,
  objectResponsesByName?: Map<string, JsonHttpResponse>,
) {
  const jsonHttpClient = new RecordingStorageJsonHttpClient(
    listingPagesByToken,
    objectResponsesByName,
  );
  return { service: buildSnapshotClientService(jsonHttpClient), jsonHttpClient };
}
