import Foundation

final class MostRecentlyUsedWindowTracker: MruTracking {
    private var windowIdentifiersOrderedByRecency: [Int] = []

    func recordFocusedWindow(_ windowIdentifier: Int) {
        if let existingIndex = windowIdentifiersOrderedByRecency.firstIndex(of: windowIdentifier) {
            windowIdentifiersOrderedByRecency.remove(at: existingIndex)
        }
        windowIdentifiersOrderedByRecency.insert(windowIdentifier, at: 0)
    }

    func sortWindowsByRecency(_ windows: [WorkspaceWindow]) -> [WorkspaceWindow] {
        var positionByWindowIdentifier: [Int: Int] = [:]
        for (position, identifier) in windowIdentifiersOrderedByRecency.enumerated() {
            positionByWindowIdentifier[identifier] = position
        }
        let unknownPosition = windowIdentifiersOrderedByRecency.count
        return windows.sorted { firstWindow, secondWindow in
            let firstPosition = positionByWindowIdentifier[firstWindow.identifier] ?? unknownPosition
            let secondPosition = positionByWindowIdentifier[secondWindow.identifier] ?? unknownPosition
            return firstPosition < secondPosition
        }
    }

    func removeStaleWindowIdentifiers(currentWindowIdentifiers: Set<Int>) {
        windowIdentifiersOrderedByRecency = windowIdentifiersOrderedByRecency.filter {
            currentWindowIdentifiers.contains($0)
        }
    }
}
