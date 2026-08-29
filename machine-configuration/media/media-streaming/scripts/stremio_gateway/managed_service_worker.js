self.addEventListener("install", () => self.skipWaiting());

const deletePrecachedResponses = async () => {
  const cacheNames = await caches.keys();
  await Promise.all(cacheNames.map((cacheName) => caches.delete(cacheName)));
  await self.clients.claim();
};

self.addEventListener("activate", (event) => {
  event.waitUntil(deletePrecachedResponses());
});
