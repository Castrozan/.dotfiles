import AppKit
import Foundation

protocol WindowProviding {
    func getFocusedWorkspaceWindows() -> [WorkspaceWindow]
    func getFocusedWindowIdentifier() -> Int?
}

protocol WindowFocusing {
    func focusWindow(withIdentifier identifier: Int)
}

protocol OverlayRendering {
    func showWithWindowsAndSelection(_ windows: [WorkspaceWindow], selectedIndex: Int)
    func updateSelectedIndex(_ selectedIndex: Int)
    func hide()
}

protocol MruTracking {
    func recordFocusedWindow(_ windowIdentifier: Int)
    func sortWindowsByRecency(_ windows: [WorkspaceWindow]) -> [WorkspaceWindow]
    func removeStaleWindowIdentifiers(currentWindowIdentifiers: Set<Int>)
}

protocol ActivationFlagWriting {
    func writeActivationFlag()
    func clearActivationFlag()
}

protocol PerformanceProfiling {
    func beginNewActivation()
    func markPhase(_ phaseName: String)
    func recordWorkspaceWindowCount(_ count: Int)
    func emitActivationReport()
}

protocol IconProviding {
    func prewarmCacheFromRunningApplications()
    func iconForApplicationName(_ applicationName: String) -> NSImage
}

protocol CommitTimeoutScheduling {
    func scheduleCommitTimeout(afterSeconds seconds: TimeInterval, onTimeout: @escaping () -> Void)
    func cancelCommitTimeout()
}

protocol SocketCommandHandling {
    func handleNextCommand()
    func handlePrevCommand()
    func handleCommitCommand()
    func handleCancelCommand()
    func recordExternallyFocusedWindow(_ windowIdentifier: Int)
}
