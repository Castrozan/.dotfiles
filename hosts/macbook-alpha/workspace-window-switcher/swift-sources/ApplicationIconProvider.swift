import AppKit
import UniformTypeIdentifiers

final class ApplicationIconProvider: IconProviding {
    private var iconCacheByApplicationName: [String: NSImage] = [:]

    func prewarmCacheFromRunningApplications() {
        let workspace = NSWorkspace.shared
        for runningApplication in workspace.runningApplications {
            guard let applicationName = runningApplication.localizedName else { continue }
            if iconCacheByApplicationName[applicationName] != nil { continue }
            if let icon = runningApplication.icon {
                iconCacheByApplicationName[applicationName] = icon
            }
        }
    }

    func iconForApplicationName(_ applicationName: String) -> NSImage {
        if let cachedIcon = iconCacheByApplicationName[applicationName] {
            return cachedIcon
        }
        let resolvedIcon = resolveIconFromRunningApplications(applicationName: applicationName)
        iconCacheByApplicationName[applicationName] = resolvedIcon
        return resolvedIcon
    }

    private func resolveIconFromRunningApplications(applicationName: String) -> NSImage {
        let workspace = NSWorkspace.shared
        for runningApplication in workspace.runningApplications {
            if runningApplication.localizedName == applicationName, let icon = runningApplication.icon {
                return icon
            }
        }
        return workspace.icon(for: UTType.application)
    }
}
