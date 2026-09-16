import Foundation

final class PerRequestColdStartProfiler {
    private let outputFilePath: String
    private let baselineNanoseconds: UInt64

    init(outputFilePath: String, baselineNanoseconds: UInt64) {
        self.outputFilePath = outputFilePath
        self.baselineNanoseconds = baselineNanoseconds
        FileManager.default.createFile(atPath: outputFilePath, contents: nil)
    }

    func recordMilestone(_ label: String) {
        let elapsedMilliseconds = Double(
            DispatchTime.now().uptimeNanoseconds - baselineNanoseconds
        ) / 1_000_000.0
        let lineContent = String(format: "%.3f\t%@\n", elapsedMilliseconds, label as NSString)
        guard let lineData = lineContent.data(using: .utf8) else { return }
        guard let fileHandle = FileHandle(forWritingAtPath: outputFilePath) else { return }
        _ = try? fileHandle.seekToEnd()
        fileHandle.write(lineData)
        try? fileHandle.close()
    }
}
