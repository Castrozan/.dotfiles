class Provider {
  constructor() {
    this.prowlarrBaseUrl = "{{prowlarrBaseUrl}}";
    this.prowlarrApiKey = "{{prowlarrApiKey}}";
    this.resultLimit = "{{resultLimit}}";
  }

  getSettings() {
    return {
      canSmartSearch: true,
      smartSearchFilters: ["batch", "episodeNumber", "resolution", "query"],
      supportsAdult: true,
      type: "main",
    };
  }

  async search(options) {
    return this.searchByQuery(this.firstTitle(options));
  }

  async smartSearch(options) {
    const parts = [this.firstTitle(options)];
    if (options.episodeNumber > 0) parts.push(String(options.episodeNumber));
    if (options.resolution) parts.push(options.resolution);
    if (options.batch) parts.push("batch");
    return this.searchByQuery(parts.filter(Boolean).join(" "));
  }

  async getTorrentInfoHash(torrent) {
    const directHash = this.validInfoHash(torrent.infoHash);
    if (directHash) return directHash;
    return this.extractInfoHash(await this.getTorrentMagnetLink(torrent));
  }

  async getTorrentMagnetLink(torrent) {
    if (torrent.magnetLink?.startsWith("magnet:?")) return torrent.magnetLink;
    const directHash = this.validInfoHash(torrent.infoHash);
    if (directHash) return this.buildMagnetLink(directHash, torrent.name);
    if (!torrent.downloadUrl?.startsWith("http")) return "";
    const response = await fetch(torrent.downloadUrl, {
      headers: {
        "X-Api-Key": this.prowlarrApiKey,
        Accept: "application/x-bittorrent",
      },
      redirect: "manual",
    });
    const location =
      response.headers.Location || response.headers.location || "";
    if (location.startsWith("magnet:?")) return location;
    if (!response.ok) return "";
    return $torrentUtils.getMagnetLinkFromTorrentData(response.text());
  }

  async getLatest() {
    return [];
  }

  firstTitle(options) {
    const titles = [
      options.query,
      options.media?.englishTitle,
      options.media?.romajiTitle,
      ...(options.media?.synonyms || []),
    ];
    return titles.find((title) => title?.trim())?.trim() || "";
  }

  async searchByQuery(query) {
    if (!query || !this.prowlarrBaseUrl || !this.prowlarrApiKey) return [];
    const url = new URL("/api/v1/search", this.normalizedBaseUrl());
    url.searchParams.set("query", query);
    const response = await fetch(url.toString(), {
      headers: {
        "X-Api-Key": this.prowlarrApiKey,
        Accept: "application/json",
      },
    });
    if (!response.ok) return [];
    const results = response.json();
    return results
      .filter((item) => item.title)
      .map((item) => this.toAnimeTorrent(item))
      .slice(0, this.parsedResultLimit());
  }

  toAnimeTorrent(item) {
    const rawMagnetUrl = item.magnetUrl || item.torrent?.magnetUrl || "";
    const rawDownloadUrl =
      item.downloadUrl || (rawMagnetUrl.startsWith("http") ? rawMagnetUrl : "");
    const magnetLink = rawMagnetUrl.startsWith("magnet:?")
      ? rawMagnetUrl
      : rawDownloadUrl.startsWith("magnet:?")
        ? rawDownloadUrl
        : "";
    const infoHash =
      this.validInfoHash(item.infoHash) ||
      this.validInfoHash(item.torrent?.infoHash) ||
      this.extractInfoHash(magnetLink);
    return {
      name: item.title,
      date: item.publishDate || "1970-01-01T00:00:00Z",
      size: Number(item.size) || 0,
      formattedSize: "",
      seeders: Number(item.seeders) || 0,
      leechers: Number(item.leechers) || 0,
      downloadCount: Number(item.grabs) || 0,
      link: this.safeLink(item.infoUrl || item.guid || ""),
      downloadUrl: rawDownloadUrl.startsWith("http")
        ? this.withoutApiKey(rawDownloadUrl)
        : "",
      magnetLink,
      infoHash,
      resolution: this.resolutionFrom(item.title),
      isBatch: /\b(batch|complete)\b/i.test(item.title),
      episodeNumber: -1,
      releaseGroup: this.releaseGroupFrom(item.title),
      isBestRelease: false,
      confirmed: false,
    };
  }

  normalizedBaseUrl() {
    return this.prowlarrBaseUrl.endsWith("/")
      ? this.prowlarrBaseUrl
      : `${this.prowlarrBaseUrl}/`;
  }

  withoutApiKey(rawUrl) {
    const url = new URL(rawUrl);
    url.searchParams.delete("apikey");
    return url.toString();
  }

  safeLink(rawLink) {
    return rawLink.startsWith("http") ? this.withoutApiKey(rawLink) : rawLink;
  }

  parsedResultLimit() {
    const value = Number(this.resultLimit);
    return Number.isInteger(value) && value > 0 ? Math.min(value, 100) : 50;
  }

  validInfoHash(value) {
    const candidate = String(value || "").trim();
    return /^(?:[a-f0-9]{40}|[a-z2-7]{32})$/i.test(candidate) ? candidate : "";
  }

  extractInfoHash(magnetLink) {
    const match = String(magnetLink || "").match(
      /xt=urn:btih:([a-f0-9]{40}|[a-z2-7]{32})/i,
    );
    return match?.[1] || "";
  }

  buildMagnetLink(infoHash, name) {
    const displayName = name ? `&dn=${encodeURIComponent(name)}` : "";
    return `magnet:?xt=urn:btih:${infoHash}${displayName}`;
  }

  resolutionFrom(name) {
    return name.match(/\b(2160p|1080p|720p|480p)\b/i)?.[1]?.toLowerCase() || "";
  }

  releaseGroupFrom(name) {
    return name.match(/^\[(.*?)\]/)?.[1] || "";
  }
}

globalThis.Provider = Provider;
