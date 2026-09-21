import Foundation

enum ApplicationCatalogTests {
  static func runAll() throws {
    let directory = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
    let applicationDirectory = directory.appendingPathComponent("home-manager-applications")
    let applicationBundle = applicationDirectory.appendingPathComponent("WezTerm.app")
    let applicationDirectoryLink = directory.appendingPathComponent("Home Manager Apps")
    try FileManager.default.createDirectory(
      at: applicationBundle, withIntermediateDirectories: true)
    try FileManager.default.createSymbolicLink(
      at: applicationDirectoryLink, withDestinationURL: applicationDirectory)
    defer { try? FileManager.default.removeItem(at: directory) }
    let linkedApplicationBundleNames = InstalledApplicationCatalog.applicationBundleURLs(
      in: applicationDirectoryLink
    ).map(\.lastPathComponent)
    precondition(linkedApplicationBundleNames == ["WezTerm.app"])
    let catalog = InstalledApplicationCatalog.discoverInstalledApplications()
    let names = catalog.applicationsSortedByDisplayName.map(\.displayName)
    precondition(names == names.sorted() && Set(names).count == names.count)
    precondition(catalog.application(named: "Finder")?.supportsLaunchingNewInstance == false)
    precondition(catalog.application(named: UUID().uuidString) == nil)
    precondition(
      catalog.applicationsSortedByDisplayName.allSatisfy { $0.bundleURL.pathExtension == "app" })
    let registry = RunningApplicationsRegistry(applicationNames: ["Terminal"])
    precondition(registry.buildDisplayLine(forApplicationNamed: "Terminal") == "● Terminal")
    precondition(registry.buildDisplayLine(forApplicationNamed: "Browser") == "  Browser")
    precondition(
      RunningApplicationsRegistry.extractApplicationName(fromDisplayLine: "● Visual Studio Code")
        == "Visual Studio Code")
    let previousPath = ProcessInfo.processInfo.environment["PATH"]
    defer {
      if let previousPath { setenv("PATH", previousPath, 1) } else { unsetenv("PATH") }
    }
    setenv("PATH", "/usr/bin:/bin", 1)
    let liveRegistry = RunningApplicationsRegistry.snapshotCurrent()
    precondition(liveRegistry.applicationNames.allSatisfy { !$0.contains("_") })
    NixPackagePathAugmenter.ensureNixPackageDirectoriesArePresentInPathEnvironment()
    precondition(ProcessInfo.processInfo.environment["PATH"]!.hasSuffix("/usr/bin:/bin"))
    setenv("PATH", "/nonexistent", 1)
    precondition(RunningApplicationsRegistry.snapshotCurrent().applicationNames.isEmpty)
    setenv("PATH", "/usr/bin:/bin", 1)
    let catalogCache = InstalledApplicationCatalogCache()
    precondition(catalogCache.currentCatalogOrEmpty().applicationsSortedByDisplayName.isEmpty)
    catalogCache.prewarmInBackground()
    let deadline = Date().addingTimeInterval(3)
    while catalogCache.currentCatalogOrEmpty().application(named: "Finder") == nil
      && Date() < deadline
    {
      Thread.sleep(forTimeInterval: 0.005)
    }
    precondition(catalogCache.currentCatalogOrEmpty().application(named: "Finder") != nil)
    catalogCache.refreshInBackground()
    catalogCache.refreshInBackground()
    let registryCache = RunningApplicationsRegistryCache()
    precondition(registryCache.currentRegistryOrEmpty().applicationNames.isEmpty)
    registryCache.prewarmInBackground()
    registryCache.refreshInBackground()
    registryCache.refreshInBackground()
    let historyDirectory = FileManager.default.temporaryDirectory.appendingPathComponent(
      UUID().uuidString)
    try FileManager.default.createDirectory(at: historyDirectory, withIntermediateDirectories: true)
    defer { try? FileManager.default.removeItem(at: historyDirectory) }
    let historyCache = LaunchHistoryStoreCache()
    historyCache.updateCachedStore(
      LaunchHistoryStore.loadOrEmpty(
        fromFilePath: historyDirectory.appendingPathComponent("history.json"))
    )
    let handler = ShowPickerCommandHandler(
      installedApplicationCatalogCache: catalogCache,
      launchHistoryStoreCache: historyCache, runningApplicationsRegistryCache: registryCache)
    handler.handleSocketCommand("unknown")
    handler.handleSocketCommand("dismiss")
    let output = historyDirectory.appendingPathComponent("display-lines")
    handler.handleSocketCommand("dump-display-lines \(output.path)")
    let displayNames = try String(contentsOf: output, encoding: .utf8).split(separator: "\n")
      .map { RunningApplicationsRegistry.extractApplicationName(fromDisplayLine: String($0)) }
    precondition(Set(displayNames) == Set(names))
  }
}
