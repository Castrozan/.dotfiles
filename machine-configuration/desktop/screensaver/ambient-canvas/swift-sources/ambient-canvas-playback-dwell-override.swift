import Foundation

enum AmbientCanvasPlaybackDwellOverride {
    static let shortestAllowedDwellSeconds = 2.0

    static func effectiveDwellSeconds(
        recordedDwellSeconds: Double,
        readFrom overrideFileUrl: URL
    ) -> Double {
        guard let requestedDwellSeconds = readRequestedDwellSeconds(overrideFileUrl) else {
            return recordedDwellSeconds
        }
        return min(
            recordedDwellSeconds,
            max(shortestAllowedDwellSeconds, requestedDwellSeconds)
        )
    }

    private static func readRequestedDwellSeconds(_ overrideFileUrl: URL) -> Double? {
        guard let overrideText = try? String(contentsOf: overrideFileUrl, encoding: .utf8) else {
            return nil
        }
        return Double(overrideText.trimmingCharacters(in: .whitespacesAndNewlines))
    }
}
