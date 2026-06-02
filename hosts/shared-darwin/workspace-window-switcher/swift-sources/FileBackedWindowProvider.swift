import Foundation

// Sources the current virtual-workspace windows from Hammerspoon (the window
// manager that replaced the Sophos-blocked AeroSpace fork). Hammerspoon owns the
// workspace assignments and writes the active workspace's windows to a JSON file;
// focusing is delegated back to Hammerspoon by writing the requested window id to
// a file Hammerspoon watches. This keeps the daemon free of any Accessibility or
// Screen-Recording grant of its own - Hammerspoon already holds those.
final class FileBackedWindowProvider: WindowProviding, WindowFocusing {
    private let workspaceWindowsFilePath = "/tmp/workspace-window-switcher-windows.json"
    private let focusRequestFilePath = "/tmp/workspace-window-switcher-focus-request"

    private func readWorkspaceState() -> [String: Any]? {
        guard let data = FileManager.default.contents(atPath: workspaceWindowsFilePath) else {
            return nil
        }
        return (try? JSONSerialization.jsonObject(with: data)) as? [String: Any]
    }

    func getFocusedWorkspaceWindows() -> [WorkspaceWindow] {
        guard let state = readWorkspaceState(),
            let windowDictionaries = state["windows"] as? [[String: Any]]
        else {
            return []
        }
        return windowDictionaries.compactMap(WorkspaceWindow.fromWindowDictionary)
    }

    func getFocusedWindowIdentifier() -> Int? {
        return readWorkspaceState()?["focused"] as? Int
    }

    func focusWindow(withIdentifier identifier: Int) {
        // A trailing nonce guarantees the file content changes on every request,
        // so Hammerspoon's path watcher fires even when focusing the same window.
        let payload = "\(identifier) \(ProcessInfo.processInfo.systemUptime)"
        try? payload.write(toFile: focusRequestFilePath, atomically: true, encoding: .utf8)
    }
}
