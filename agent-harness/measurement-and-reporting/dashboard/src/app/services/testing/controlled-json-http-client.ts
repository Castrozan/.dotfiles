import type {
  JsonHttpClientPort,
  JsonHttpResponse,
} from '../../dependencies/json-http-client/json-http-client.port';

export interface PendingSnapshotRequest {
  readonly url: string;
  readonly respond: (response: JsonHttpResponse) => void;
  readonly fail: (error: Error) => void;
}

export class ControlledJsonHttpClient implements JsonHttpClientPort {
  readonly pendingSnapshotRequests: PendingSnapshotRequest[] = [];
  readonly requestedSnapshotUrls: string[] = [];
  readonly requestedListingUrls: string[] = [];
  activeSnapshotRequestCount = 0;
  peakSnapshotRequestCount = 0;

  constructor(private readonly listingPagesByToken: Map<string | null, JsonHttpResponse>) {}

  get requestedPageTokens(): (string | null)[] {
    return this.requestedListingUrls.map((url) => new URL(url).searchParams.get('pageToken'));
  }

  getJson(url: string): Promise<JsonHttpResponse> {
    if (url.includes('/o?')) {
      return this.respondWithListingPage(url);
    }
    this.requestedSnapshotUrls.push(url);
    this.activeSnapshotRequestCount += 1;
    this.peakSnapshotRequestCount = Math.max(
      this.peakSnapshotRequestCount,
      this.activeSnapshotRequestCount,
    );
    return new Promise((resolve, reject) => {
      const settle = () => {
        this.activeSnapshotRequestCount -= 1;
        this.pendingSnapshotRequests.splice(this.pendingSnapshotRequests.indexOf(request), 1);
      };
      const request: PendingSnapshotRequest = {
        url,
        respond: (response) => {
          settle();
          resolve(response);
        },
        fail: (error) => {
          settle();
          reject(error);
        },
      };
      this.pendingSnapshotRequests.push(request);
    });
  }

  private async respondWithListingPage(url: string): Promise<JsonHttpResponse> {
    const pageToken = new URL(url).searchParams.get('pageToken');
    if (this.requestedPageTokens.includes(pageToken)) {
      throw new Error('Unexpected repeated listing request');
    }
    this.requestedListingUrls.push(url);
    return this.listingPagesByToken.get(pageToken) ?? { ok: false, status: 404, body: null };
  }
}

export function okResponse(body: unknown): JsonHttpResponse {
  return { ok: true, status: 200, body };
}

export function settleMicrotasks(): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, 0));
}
