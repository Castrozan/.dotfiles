import Foundation

enum LaunchHistoryTests {
  static func runAll() throws {
    let directory = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
    defer { try? FileManager.default.removeItem(at: directory) }
    let file = directory.appendingPathComponent("nested/history.json")
    var history = LaunchHistoryStore.loadOrEmpty(fromFilePath: file)
    precondition(history.entriesByApplicationName.isEmpty)
    precondition(history.frecencyScore(forApplicationNamed: "missing") == nil)
    precondition(history.sortApplicationNamesByFrecency(["zeta", "Alpha"]) == ["Alpha", "zeta"])
    history.recordLaunchOfApplication(named: "Terminal")
    history.recordLaunchOfApplication(named: "Terminal")
    history.recordLaunchOfApplication(named: "Browser")
    let restored = LaunchHistoryStore.loadOrEmpty(fromFilePath: file)
    precondition(restored.entriesByApplicationName["Terminal"]?.launchCount == 2)
    precondition(
      restored.sortApplicationNamesByFrecency(["zeta", "Browser", "Alpha", "Terminal"])
        == ["Terminal", "Browser", "Alpha", "zeta"])
    let score = restored.frecencyScore(forApplicationNamed: "Terminal")!
    precondition(score > 1.99 && score <= 2)
    let cache = LaunchHistoryStoreCache()
    cache.updateCachedStore(restored)
    precondition(cache.currentStoreOrFreshlyLoadedFromDisk().entriesByApplicationName.count == 2)
    try Data("invalid".utf8).write(to: file)
    precondition(
      LaunchHistoryStore.loadOrEmpty(fromFilePath: file).entriesByApplicationName.isEmpty)
    var unwritable = LaunchHistoryStore.loadOrEmpty(
      fromFilePath: file.appendingPathComponent("child"))
    unwritable.recordLaunchOfApplication(named: "Retained in memory")
    precondition(unwritable.entriesByApplicationName.count == 1)
    let oldEntry = [
      "Old": LaunchHistoryEntry(
        launchCount: 8, lastLaunchedAt: Date().timeIntervalSince1970 - 7 * 86400)
    ]
    try JSONEncoder().encode(oldEntry).write(to: file)
    let decayed = LaunchHistoryStore.loadOrEmpty(fromFilePath: file).frecencyScore(
      forApplicationNamed: "Old")!
    precondition(abs(decayed - 4) < 0.01)
  }
}
