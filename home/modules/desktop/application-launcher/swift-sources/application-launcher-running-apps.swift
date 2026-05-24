import Foundation
import os

struct RunningApplicationsRegistry {
    let applicationNames: Set<String>

    static let runningIndicator = "\u{25CF}"
    static let notRunningIndicator = " "

    private static let logger = Logger(
        subsystem: "com.dotfiles.application-launcher",
        category: "running-apps"
    )

    static func snapshotCurrent() -> RunningApplicationsRegistry {
        guard let lsappinfoOutput = readVisibleProcessListOutputFromLsappinfo() else {
            return RunningApplicationsRegistry(applicationNames: [])
        }
        let quotedWordPattern = #/"(\w+)"/#
        var applicationNames = Set<String>()
        for match in lsappinfoOutput.matches(of: quotedWordPattern) {
            let nameWithUnderscores = String(match.output.1)
            let nameWithSpaces = nameWithUnderscores.replacingOccurrences(of: "_", with: " ")
            applicationNames.insert(nameWithSpaces)
        }
        return RunningApplicationsRegistry(applicationNames: applicationNames)
    }

    func buildDisplayLine(forApplicationNamed applicationName: String) -> String {
        let indicator = applicationNames.contains(applicationName)
            ? Self.runningIndicator
            : Self.notRunningIndicator
        return "\(indicator) \(applicationName)"
    }

    static func extractApplicationName(fromDisplayLine displayLine: String) -> String {
        return String(displayLine.dropFirst(2))
    }

    private static func readVisibleProcessListOutputFromLsappinfo() -> String? {
        let lsappinfoProcess = Process()
        lsappinfoProcess.executableURL = URL(fileURLWithPath: "/usr/bin/env")
        lsappinfoProcess.arguments = ["lsappinfo", "visibleProcessList"]
        let standardOutputPipe = Pipe()
        lsappinfoProcess.standardOutput = standardOutputPipe
        lsappinfoProcess.standardError = Pipe()
        do {
            try lsappinfoProcess.run()
            lsappinfoProcess.waitUntilExit()
        } catch {
            logger.error("lsappinfo run failed: \(error.localizedDescription)")
            return nil
        }
        guard lsappinfoProcess.terminationStatus == 0 else {
            logger.error("lsappinfo exited with status \(lsappinfoProcess.terminationStatus)")
            return nil
        }
        let outputData = standardOutputPipe.fileHandleForReading.readDataToEndOfFile()
        return String(data: outputData, encoding: .utf8)
    }
}
