import { isJsonObject, isOptionalString } from './json-value-guards';

export interface StorageObjectListing {
  items?: { name: string }[];
  nextPageToken?: string;
}

function isStorageObject(value: unknown): value is { name: string } {
  if (!isJsonObject(value)) {
    return false;
  }
  const { name } = value;
  return typeof name === 'string';
}

function isStorageObjectList(value: unknown): value is { name: string }[] | undefined {
  return value === undefined || (Array.isArray(value) && value.every(isStorageObject));
}

function isStorageObjectListing(value: unknown): value is StorageObjectListing {
  if (!isJsonObject(value)) {
    return false;
  }
  const { items, nextPageToken } = value;
  return isStorageObjectList(items) && isOptionalString(nextPageToken);
}

export function parseStorageObjectListing(value: unknown): StorageObjectListing {
  if (!isStorageObjectListing(value)) {
    throw new Error('Invalid snapshot listing response');
  }
  return value;
}
