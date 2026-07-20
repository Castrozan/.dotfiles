import Foundation

enum AmbientCanvasPlaybackDwellOverride {
    static let overrideFileName = "playback-dwell-seconds"
    static let shortestAllowedDwellSeconds = 2.0

    static func effectiveDwellSeconds(
        recordedDwellSeconds: Double,
        besideRecordedLoop recordedLoopFileUrl: URL
    ) -> Double {
        guard let requestedDwellSeconds = readRequestedDwellSeconds(recordedLoopFileUrl) else {
            return recordedDwellSeconds
        }
        return min(
            recordedDwellSeconds,
            max(shortestAllowedDwellSeconds, requestedDwellSeconds)
        )
    }

    private static func readRequestedDwellSeconds(_ recordedLoopFileUrl: URL) -> Double? {
        let overrideUrl = recordedLoopFileUrl
            .deletingLastPathComponent()
            .appendingPathComponent(overrideFileName)
        guard let overrideText = try? String(contentsOf: overrideUrl, encoding: .utf8) else {
            return nil
        }
        return Double(overrideText.trimmingCharacters(in: .whitespacesAndNewlines))
    }
}
