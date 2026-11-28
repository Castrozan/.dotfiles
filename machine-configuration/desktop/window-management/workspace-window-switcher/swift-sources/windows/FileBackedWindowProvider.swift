import Foundation

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
        let payload = "\(identifier) \(ProcessInfo.processInfo.systemUptime)"
        try? payload.write(toFile: focusRequestFilePath, atomically: true, encoding: .utf8)
    }
}
