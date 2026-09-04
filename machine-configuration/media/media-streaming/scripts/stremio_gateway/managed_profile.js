(() => {
  const managedStreamingServerUrl = __STREMIO_MANAGED_STREAMING_SERVER_URL__;
  const managedProfileConfiguration = __STREMIO_MANAGED_PROFILE_CONFIGURATION__;

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

  const officialTransportUrl = (addonDefinition) =>
    typeof addonDefinition.transportUrl === "string"
      ? addonDefinition.transportUrl
      : new URL(
          addonDefinition.streamingServerPath,
          managedStreamingServerUrl,
        ).toString();

  const loadOfficialAddonEntry = async (addonDefinition) => {
    const transportUrl = officialTransportUrl(addonDefinition);
    try {
      const response = await window.fetch(transportUrl);
      if (!response.ok) {
        return null;
      }
      return {
        manifest: await response.json(),
        transportUrl,
        flags: addonDefinition.flags,
      };
    } catch {
      return null;
    }
  };

  const configuredTransportPath = (transportPath, configuration) => {
    if (configuration === undefined) {
      return transportPath;
    }
    const encodedConfiguration = window.btoa(JSON.stringify(configuration));
    return transportPath.replace(
      "/manifest.json",
      `/${encodedConfiguration}/manifest.json`,
    );
  };

  const managedAddonEntries = managedProfileConfiguration.managedAddons.map(
    ({ manifest, transportPath, configuration }) => ({
      manifest,
      transportUrl: `${window.location.origin}${configuredTransportPath(transportPath, configuration)}`,
      flags: { official: false, protected: false },
    }),
  );

  const officialEntryByTransportUrl = (profile) =>
    new Map(
      profile?.addons
        ?.filter((addon) => addon?.flags?.official === true)
        .map((addon) => [addon.transportUrl, addon]) ?? [],
    );

  const loadStoredOfficialAddonEntries = (profile) => {
    const storedOfficialEntries = officialEntryByTransportUrl(profile);
    return managedProfileConfiguration.officialAddons
      .map((addonDefinition) =>
        storedOfficialEntries.get(officialTransportUrl(addonDefinition)),
      )
      .filter((addon) => addon !== undefined);
  };

  const loadOfficialAddonEntries = async (profile) => {
    const storedOfficialEntries = officialEntryByTransportUrl(profile);
    const loadedEntries = await Promise.all(
      managedProfileConfiguration.officialAddons.map(loadOfficialAddonEntry),
    );
    return managedProfileConfiguration.officialAddons
      .map(
        (addonDefinition, index) =>
          loadedEntries[index] ??
          storedOfficialEntries.get(officialTransportUrl(addonDefinition)),
      )
      .filter((addon) => addon !== undefined && addon !== null);
  };

  const managedServerUrls = () => {
    const storedServerUrls = parseStoredRecord("streaming_server_urls");
    const previousTimestamp =
      storedServerUrls?.items?.[managedStreamingServerUrl];
    return {
      uid: storedServerUrls?.uid ?? null,
      items: {
        [managedStreamingServerUrl]:
          typeof previousTimestamp === "string"
            ? previousTimestamp
            : new Date().toISOString(),
      },
    };
  };

  const storeManagedProfile = (storedProfile, officialAddonEntries) => {
    const profile =
      storedProfile === null ||
      !Array.isArray(storedProfile.addons) ||
      typeof storedProfile.settings !== "object" ||
      storedProfile.settings === null
        ? {
            auth: null,
            addons: [],
            addonsLocked: true,
            settings: managedProfileConfiguration.defaultSettings,
          }
        : storedProfile;
    const managedProfile = {
      ...profile,
      addons: [...officialAddonEntries, ...managedAddonEntries],
      addonsLocked: true,
      settings: {
        ...profile.settings,
        audioLanguage:
          managedProfileConfiguration.defaultSettings.audioLanguage,
        secondaryAudioLanguage:
          managedProfileConfiguration.defaultSettings.secondaryAudioLanguage,
        streamingServerUrl: managedStreamingServerUrl,
      },
    };
    const serializedProfile = JSON.stringify(managedProfile);
    const serializedServerUrls = JSON.stringify(managedServerUrls());
    const profileChanged =
      serializedProfile !== window.localStorage.getItem("profile");
    const serverUrlsChanged =
      serializedServerUrls !==
      window.localStorage.getItem("streaming_server_urls");

    if (profileChanged) {
      window.localStorage.setItem("profile", serializedProfile);
      window.localStorage.setItem(
        "schema_version",
        managedProfileConfiguration.schemaVersion,
      );
    }
    if (serverUrlsChanged) {
      window.localStorage.setItem(
        "streaming_server_urls",
        serializedServerUrls,
      );
    }
    return profileChanged || serverUrlsChanged;
  };

  const synchronizeManagedProfile = async () => {
    const storedProfile = parseStoredRecord("profile");
    const storedOfficialAddonEntries =
      loadStoredOfficialAddonEntries(storedProfile);
    if (storeManagedProfile(storedProfile, storedOfficialAddonEntries)) {
      window.stop();
      window.location.reload();
      return;
    }
    const officialAddonEntries = await loadOfficialAddonEntries(storedProfile);
    if (storeManagedProfile(storedProfile, officialAddonEntries)) {
      window.location.reload();
    }
  };

  void synchronizeManagedProfile();
})();
