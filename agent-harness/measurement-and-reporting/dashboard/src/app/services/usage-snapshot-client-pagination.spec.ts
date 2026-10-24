import { TestBed } from '@angular/core/testing';
import {
  JSON_HTTP_CLIENT,
  type JsonHttpResponse,
} from '../dependencies/json-http-client/json-http-client.port';
import { ControlledJsonHttpClient, okResponse } from './testing/controlled-json-http-client';
import { UsageSnapshotClientService } from './usage-snapshot-client.service';

function buildControlledService(listingPagesByToken: Map<string | null, JsonHttpResponse>) {
  const jsonHttpClient = new ControlledJsonHttpClient(listingPagesByToken);
  TestBed.configureTestingModule({
    providers: [{ provide: JSON_HTTP_CLIENT, useValue: jsonHttpClient }],
  });
  return { service: TestBed.inject(UsageSnapshotClientService), jsonHttpClient };
}

describe('UsageSnapshotClientService listing pagination', () => {
  it('lists with the configured bucket and prefix', async () => {
    const { service, jsonHttpClient } = buildControlledService(
      new Map<string | null, JsonHttpResponse>([[null, okResponse({})]]),
    );

    await service.fetchAllSnapshots();

    const listingUrl = new URL(jsonHttpClient.requestedListingUrls[0]);
    expect(listingUrl.origin + listingUrl.pathname).toBe(
      'https://storage.googleapis.com/storage/v1/b/zg-url-shortener-2026-dotfiles-usage-snapshots/o',
    );
    expect(listingUrl.searchParams.get('prefix')).toBe('snapshots/');
  });

  it('rejects a listing page that names its own token as the next page', async () => {
    const { service, jsonHttpClient } = buildControlledService(
      new Map<string | null, JsonHttpResponse>([
        [null, okResponse({ items: [{ name: 'a.json' }], nextPageToken: 'loop' })],
        ['loop', okResponse({ items: [{ name: 'b.json' }], nextPageToken: 'loop' })],
      ]),
    );

    await expect(service.fetchAllSnapshots()).rejects.toThrow('pagination cycle');
    expect(jsonHttpClient.requestedPageTokens).toEqual([null, 'loop']);
    expect(jsonHttpClient.requestedSnapshotUrls).toEqual([]);
  });

  it('rejects a listing whose continuation tokens cycle through several pages', async () => {
    const { service, jsonHttpClient } = buildControlledService(
      new Map<string | null, JsonHttpResponse>([
        [null, okResponse({ nextPageToken: 'first' })],
        ['first', okResponse({ nextPageToken: 'second' })],
        ['second', okResponse({ nextPageToken: 'third' })],
        ['third', okResponse({ nextPageToken: 'first' })],
      ]),
    );

    await expect(service.fetchAllSnapshots()).rejects.toThrow('pagination cycle');
    expect(jsonHttpClient.requestedPageTokens).toEqual([null, 'first', 'second', 'third']);
  });

  it('treats empty listing pages and an empty continuation token as a finished listing', async () => {
    const { service, jsonHttpClient } = buildControlledService(
      new Map<string | null, JsonHttpResponse>([
        [null, okResponse({ items: [], nextPageToken: 'next' })],
        ['next', okResponse({ nextPageToken: '' })],
      ]),
    );

    await expect(service.fetchAllSnapshots()).resolves.toEqual([]);
    expect(jsonHttpClient.requestedPageTokens).toEqual([null, 'next']);
    expect(jsonHttpClient.requestedSnapshotUrls).toEqual([]);
  });

  it('rejects the load when a later listing page fails', async () => {
    const { service, jsonHttpClient } = buildControlledService(
      new Map<string | null, JsonHttpResponse>([
        [null, okResponse({ items: [{ name: 'a.json' }], nextPageToken: 'missing' })],
      ]),
    );

    await expect(service.fetchAllSnapshots()).rejects.toThrow('status 404');
    expect(jsonHttpClient.requestedSnapshotUrls).toEqual([]);
  });

  it('rejects the load when the listing transport fails', async () => {
    const { service, jsonHttpClient } = buildControlledService(new Map());
    vi.spyOn(jsonHttpClient, 'getJson').mockRejectedValueOnce(new TypeError('network unavailable'));

    await expect(service.fetchAllSnapshots()).rejects.toThrow('network unavailable');
  });
});
