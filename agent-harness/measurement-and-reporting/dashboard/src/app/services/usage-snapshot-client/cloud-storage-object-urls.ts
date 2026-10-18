const cloudStorageJsonApiBucketsUrl = 'https://storage.googleapis.com/storage/v1/b';

export function buildObjectListingUrl(
  bucket: string,
  objectPrefix: string,
  pageToken: string | undefined,
): string {
  const listUrl = new URL(`${cloudStorageJsonApiBucketsUrl}/${bucket}/o`);
  listUrl.searchParams.set('prefix', objectPrefix);
  listUrl.searchParams.set('fields', 'items(name),nextPageToken');
  if (pageToken) {
    listUrl.searchParams.set('pageToken', pageToken);
  }
  return listUrl.toString();
}

export function buildObjectMediaUrl(bucket: string, objectName: string): string {
  return `${cloudStorageJsonApiBucketsUrl}/${bucket}/o/${encodeURIComponent(objectName)}?alt=media`;
}
