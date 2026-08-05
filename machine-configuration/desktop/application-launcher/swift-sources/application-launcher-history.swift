import Foundation
import os

struct LaunchHistoryEntry: Codable {
    var launchCount: Int
    var lastLaunchedAt: TimeInterval

    enum CodingKeys: String, CodingKey {
        case launchCount = "launch_count"
        case lastLaunchedAt = "last_launched_at"
    }
}

struct LaunchHistoryStore {
    private(set) var entriesByApplicationName: [String: LaunchHistoryEntry]
    private let filePath: URL
    private let frecencyHalfLifeDays: Double

    private static let logger = Logger(
        subsystem: "com.dotfiles.application-launcher",
        category: "history"
    )

    static let defaultFilePath: URL = FileManager.default.homeDirectoryForCurrentUser
        .appendingPathComponent(".local/share/application-launcher/history.json")

    static let defaultFrecencyHalfLifeDays: Double = 7

    static func loadOrEmpty(
        fromFilePath filePath: URL = defaultFilePath,
        frecencyHalfLifeDays: Double = defaultFrecencyHalfLifeDays
    ) -> LaunchHistoryStore {
        let entries: [String: LaunchHistoryEntry]
        do {
            let fileContents = try Data(contentsOf: filePath)
            entries = try JSONDecoder().decode([String: LaunchHistoryEntry].self, from: fileContents)
        } catch CocoaError.fileReadNoSuchFile, CocoaError.fileNoSuchFile {
            entries = [:]
        } catch {
            logger.error("history load failed, starting empty: \(error.localizedDescription)")
            entries = [:]
        }
        return LaunchHistoryStore(
            entriesByApplicationName: entries,
            filePath: filePath,
            frecencyHalfLifeDays: frecencyHalfLifeDays
        )
    }

    mutating func recordLaunchOfApplication(named applicationName: String) {
        var entry = entriesByApplicationName[applicationName]
            ?? LaunchHistoryEntry(launchCount: 0, lastLaunchedAt: 0)
        entry.launchCount += 1
        entry.lastLaunchedAt = Date().timeIntervalSince1970
        entriesByApplicationName[applicationName] = entry
        persistEntriesToDisk()
    }

    func frecencyScore(forApplicationNamed applicationName: String) -> Double? {
        guard let entry = entriesByApplicationName[applicationName] else { return nil }
        let daysSinceLastLaunch = (Date().timeIntervalSince1970 - entry.lastLaunchedAt) / 86400
        let recencyWeight = pow(2.0, -daysSinceLastLaunch / frecencyHalfLifeDays)
        return Double(entry.launchCount) * recencyWeight
    }

    func sortApplicationNamesByFrecency(_ applicationNames: [String]) -> [String] {
        return applicationNames.sorted { leftName, rightName in
            switch (frecencyScore(forApplicationNamed: leftName),
                    frecencyScore(forApplicationNamed: rightName)) {
            case let (.some(leftScore), .some(rightScore)):
                return leftScore > rightScore
            case (.some, .none):
                return true
            case (.none, .some):
                return false
            case (.none, .none):
                return leftName.lowercased() < rightName.lowercased()
            }
        }
    }

    private func persistEntriesToDisk() {
        let parentDirectory = filePath.deletingLastPathComponent()
        do {
            try FileManager.default.createDirectory(
                at: parentDirectory,
                withIntermediateDirectories: true
            )
            let encoder = JSONEncoder()
            encoder.outputFormatting = .prettyPrinted
            let encodedEntries = try encoder.encode(entriesByApplicationName)
            try encodedEntries.write(to: filePath)
        } catch {
            Self.logger.error("history save failed: \(error.localizedDescription)")
        }
    }
}
