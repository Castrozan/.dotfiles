import Foundation

struct MonotonicTimestamp: Equatable {
    let nanoseconds: UInt64

    static func now() -> MonotonicTimestamp {
        return MonotonicTimestamp(nanoseconds: DispatchTime.now().uptimeNanoseconds)
    }

    func millisecondsSince(_ baseline: MonotonicTimestamp) -> Double {
        return Double(nanoseconds &- baseline.nanoseconds) / 1_000_000.0
    }
}

final class ActivationPerformanceProfiler: PerformanceProfiling {
    private static let phaseNamesInReportOrder: [String] = [
        "worker_started",
        "ipc_workspace_done",
        "ipc_focus_done",
        "main_callback",
        "mru_sort_done",
        "overlay_visible",
    ]

    private let logFilePath: String
    private let lock = NSLock()
    private var timestampsByPhaseName: [String: MonotonicTimestamp] = [:]
    private var workspaceWindowCount: Int = 0

    init(logFilePath: String) {
        self.logFilePath = logFilePath
    }

    func beginNewActivation() {
        lock.lock()
        timestampsByPhaseName = [:]
        workspaceWindowCount = 0
        timestampsByPhaseName["begin"] = MonotonicTimestamp.now()
        lock.unlock()
    }

    func markPhase(_ phaseName: String) {
        lock.lock()
        if timestampsByPhaseName["begin"] != nil {
            timestampsByPhaseName[phaseName] = MonotonicTimestamp.now()
        }
        lock.unlock()
    }

    func recordWorkspaceWindowCount(_ count: Int) {
        lock.lock()
        workspaceWindowCount = count
        lock.unlock()
    }

    func emitActivationReport() {
        lock.lock()
        let timestampsSnapshot = timestampsByPhaseName
        let countSnapshot = workspaceWindowCount
        timestampsByPhaseName = [:]
        workspaceWindowCount = 0
        lock.unlock()

        guard let baselineTimestamp = timestampsSnapshot["begin"] else { return }
        var lineParts: [String] = ["windows=\(countSnapshot)"]
        for phaseName in Self.phaseNamesInReportOrder {
            if let phaseTimestamp = timestampsSnapshot[phaseName] {
                let milliseconds = phaseTimestamp.millisecondsSince(baselineTimestamp)
                lineParts.append("\(phaseName)=\(String(format: "%.3f", milliseconds))")
            }
        }
        appendLineToLogFile(lineParts.joined(separator: " ") + "\n")
    }

    private func appendLineToLogFile(_ line: String) {
        let data = Data(line.utf8)
        if let fileHandle = FileHandle(forWritingAtPath: logFilePath) {
            fileHandle.seekToEndOfFile()
            fileHandle.write(data)
            try? fileHandle.close()
        } else {
            FileManager.default.createFile(atPath: logFilePath, contents: data)
        }
    }
}
