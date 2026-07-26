import Foundation

enum AmbientCanvasPlaybackDwellOverride {
    static let overrideFileName = "playback-dwell-seconds"
    static let shortestAllowedDwellSeconds = 2.0

    static func effectiveDwellSeconds(
        recordedDwellSeconds: Double,
        besideManifestFile manifestFileUrl: URL
    ) -> Double {
        guard let requestedDwellSeconds = readRequestedDwellSeconds(manifestFileUrl) else {
            return recordedDwellSeconds
        }
        return min(
            recordedDwellSeconds,
            max(shortestAllowedDwellSeconds, requestedDwellSeconds)
        )
    }

    private static func readRequestedDwellSeconds(_ manifestFileUrl: URL) -> Double? {
        let overrideUrl = manifestFileUrl
            .deletingLastPathComponent()
            .appendingPathComponent(overrideFileName)
        guard let overrideText = try? String(contentsOf: overrideUrl, encoding: .utf8) else {
            return nil
        }
        return Double(overrideText.trimmingCharacters(in: .whitespacesAndNewlines))
    }
}
