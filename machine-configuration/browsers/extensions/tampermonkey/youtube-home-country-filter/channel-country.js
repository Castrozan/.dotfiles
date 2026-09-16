const youtubeChannelCountries = (() => {
  "use strict";
  const storageKey = "youtube-home-country-cache-v1";
  const cache = readCache();
  let retryAfter = 0;

  function readCache() {
    try {
      return new Map(
        JSON.parse(localStorage.getItem(storageKey) || "[]").slice(-256),
      );
    } catch {
      return new Map();
    }
  }

  function findField(value, field) {
    if (!value || typeof value !== "object") return undefined;
    if (Object.hasOwn(value, field)) return value[field];
    for (const child of Object.values(value)) {
      const found = findField(child, field);
      if (found !== undefined) return found;
    }
  }

  function cached(identifier) {
    const entry = cache.get(identifier);
    if (entry?.expires > Date.now()) {
      if (entry.country === null || typeof entry.country === "string")
        return entry.country;
    }
    return undefined;
  }

  function remember(identifier, country, lifetime) {
    cache.delete(identifier);
    cache.set(identifier, { country, expires: Date.now() + lifetime });
    while (cache.size > 256) cache.delete(cache.keys().next().value);
    try {
      localStorage.setItem(storageKey, JSON.stringify([...cache]));
    } catch {
      return;
    }
  }

  async function browse(payload, fields) {
    const clientVersion = window.ytcfg?.get("INNERTUBE_CLIENT_VERSION");
    if (!clientVersion) throw new Error("YouTube client is not ready");
    const response = await fetch(
      `/youtubei/v1/browse?prettyPrint=false&fields=${encodeURIComponent(fields)}`,
      {
        method: "POST",
        credentials: "omit",
        signal: AbortSignal.timeout(10000),
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          context: {
            client: { clientName: "WEB", clientVersion, hl: "en", gl: "US" },
          },
          ...payload,
        }),
      },
    );
    if (!response.ok) {
      if (response.status === 429) retryAfter = Date.now() + 300000;
      throw new Error(`YouTube country lookup: HTTP ${response.status}`);
    }
    return response.json();
  }

  async function lookup(identifier) {
    const country = cached(identifier);
    if (country !== undefined) return country;
    if (retryAfter > Date.now()) return null;
    try {
      const header = await browse(
        { browseId: identifier },
        "header/pageHeaderRenderer/content/pageHeaderViewModel/description",
      );
      const continuation = findField(header, "continuationCommand")?.token;
      if (!continuation)
        throw new Error("YouTube About continuation is missing");
      const response = await browse(
        { continuation },
        "onResponseReceivedEndpoints/appendContinuationItemsAction/continuationItems/aboutChannelRenderer/metadata/aboutChannelViewModel(channelId,country)",
      );
      const about = findField(response, "aboutChannelViewModel");
      if (about?.channelId !== identifier)
        throw new Error("YouTube About channel does not match");
      const resolved = typeof about.country === "string" ? about.country : null;
      remember(identifier, resolved, resolved ? 604800000 : 86400000);
      return resolved;
    } catch {
      remember(identifier, null, 300000);
      return null;
    }
  }
  return { cached, lookup };
})();
