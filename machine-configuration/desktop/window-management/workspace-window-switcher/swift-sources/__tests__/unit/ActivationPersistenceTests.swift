import Foundation

enum ActivationPersistenceTests {
  static func runAll() throws {
    let directory = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
    try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
    defer { try? FileManager.default.removeItem(at: directory) }
    let flagPath = directory.appendingPathComponent("active").path
    let flag = ActivationFlagFileWriter(flagFilePath: flagPath)
    flag.clearActivationFlag()
    flag.writeActivationFlag()
    precondition(FileManager.default.fileExists(atPath: flagPath))
    flag.clearActivationFlag()
    precondition(!FileManager.default.fileExists(atPath: flagPath))
    let file = directory.appendingPathComponent("timings")
    let profiler = ActivationPerformanceProfiler(logFilePath: file.path)
    profiler.markPhase("worker_started")
    profiler.emitActivationReport()
    precondition(!FileManager.default.fileExists(atPath: file.path))
    for count in [3, 1] {
      profiler.beginNewActivation()
      profiler.recordWorkspaceWindowCount(count)
      profiler.markPhase("worker_started")
      profiler.markPhase("overlay_visible")
      profiler.emitActivationReport()
    }
    profiler.emitActivationReport()
    let lines = try String(contentsOf: file, encoding: .utf8).split(separator: "\n")
    precondition(
      lines.count == 2 && lines[0].hasPrefix("windows=3 ") && lines[1].hasPrefix("windows=1 "))
    precondition(
      lines.allSatisfy { $0.contains("worker_started=") && $0.contains("overlay_visible=") })
    precondition(
      MonotonicTimestamp(nanoseconds: 3_000_000).millisecondsSince(
        MonotonicTimestamp(nanoseconds: 1_000_000)) == 2)
    let scheduler = CommitTimeoutTimerScheduler()
    var fired = 0
    scheduler.scheduleCommitTimeout(afterSeconds: 0.01) { fired += 1 }
    scheduler.cancelCommitTimeout()
    RunLoop.main.run(until: Date().addingTimeInterval(0.03))
    precondition(fired == 0)
    scheduler.scheduleCommitTimeout(afterSeconds: 0.01) { fired += 1 }
    TestMainRunLoop.until { fired == 1 }
    scheduler.cancelCommitTimeout()
  }
}
