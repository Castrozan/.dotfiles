(() => {
  const managedStreamingServerUrl = __STREMIO_MANAGED_STREAMING_SERVER_URL__;
  const managedAddonDefinitions = [
    {
      manifest: {
        id: "com.lucaszanoni.prowlarr-streams",
        version: "1.0.0",
        name: "Prowlarr Streams",
        contactEmail: null,
        description: "Instant private movie and TV streams from Prowlarr",
        logo: null,
        background: null,
        types: ["movie", "series"],
        resources: ["stream"],
        idPrefixes: ["tt"],
        catalogs: [],
        addonCatalogs: [],
        behaviorHints: {
          adult: false,
          p2p: true,
          configurable: false,
          configurationRequired: false,
        },
      },
      transportPath: "/prowlarr/manifest.json",
    },
    {
      manifest: {
        id: "stremio.comet.fast",
        version: "2.0.0",
        name: "Comet",
        contactEmail: null,
        description: "Stremio's fastest torrent/debrid search add-on.",
        logo: "https://raw.githubusercontent.com/g0ldyy/comet/refs/heads/main/comet/assets/icon.png",
        background:
          "https://raw.githubusercontent.com/g0ldyy/comet/refs/heads/main/comet/assets/background.png",
        types: ["movie", "series", "anime", "other"],
        resources: [
          {
            name: "stream",
            types: ["movie", "series"],
            idPrefixes: ["tt", "kitsu"],
          },
        ],
        idPrefixes: null,
        catalogs: [],
        addonCatalogs: [],
        behaviorHints: {
          adult: false,
          p2p: false,
          configurable: true,
          configurationRequired: false,
        },
      },
      transportPath: "/comet/manifest.json",
    },
  ];

  const parseStoredRecord = (storageKey) => {
    const serializedRecord = window.localStorage.getItem(storageKey);
    if (serializedRecord === null) {
      return null;
    }
    try {
      const record = JSON.parse(serializedRecord);
      return typeof record === "object" && record !== null ? record : null;
    } catch {
      return null;
    }
  };

  const managedAddonEntries = managedAddonDefinitions.map(
    ({ manifest, transportPath }) => ({
      manifest,
      transportUrl: `${window.location.origin}${transportPath}`,
      flags: { official: false, protected: false },
    }),
  );

  const reconcileManagedProfile = () => {
    const serializedProfile = window.localStorage.getItem("profile");
    const profile = parseStoredRecord("profile");
    if (
      serializedProfile === null ||
      profile === null ||
      !Array.isArray(profile.addons) ||
      typeof profile.settings !== "object" ||
      profile.settings === null
    ) {
      return null;
    }

    const officialAddonEntries = profile.addons.filter(
      (addon) => addon?.flags?.official === true,
    );
    const managedProfile = {
      ...profile,
      addons: [...officialAddonEntries, ...managedAddonEntries],
      addonsLocked: true,
      settings: {
        ...profile.settings,
        streamingServerUrl: managedStreamingServerUrl,
      },
    };
    const serializedManagedProfile = JSON.stringify(managedProfile);
    const storedServerUrls = parseStoredRecord("streaming_server_urls");
    const previousTimestamp =
      storedServerUrls?.items?.[managedStreamingServerUrl];
    const managedServerUrls = {
      uid: storedServerUrls?.uid ?? null,
      items: {
        [managedStreamingServerUrl]:
          typeof previousTimestamp === "string"
            ? previousTimestamp
            : new Date().toISOString(),
      },
    };
    const serializedManagedServerUrls = JSON.stringify(managedServerUrls);
    const profileChanged = serializedManagedProfile !== serializedProfile;
    const serverUrlsChanged =
      serializedManagedServerUrls !==
      window.localStorage.getItem("streaming_server_urls");

    if (profileChanged) {
      window.localStorage.setItem("profile", serializedManagedProfile);
    }
    if (serverUrlsChanged) {
      window.localStorage.setItem(
        "streaming_server_urls",
        serializedManagedServerUrls,
      );
    }
    return profileChanged || serverUrlsChanged;
  };

  const applyManagedProfile = () => {
    const changed = reconcileManagedProfile();
    if (changed === true) {
      window.location.reload();
    }
    return changed !== null;
  };

  if (!applyManagedProfile()) {
    let attemptCount = 0;
    const profileInitializationTimer = window.setInterval(() => {
      attemptCount += 1;
      if (applyManagedProfile() || attemptCount >= 100) {
        window.clearInterval(profileInitializationTimer);
      }
    }, 50);
  }
})();
