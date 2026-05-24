import AppKit
import os

enum ApplicationLaunchAction {
    private static let logger = Logger(
        subsystem: "com.dotfiles.application-launcher",
        category: "launch"
    )

    static func launchApplication(_ installedApplication: InstalledApplication) {
        let configuration = NSWorkspace.OpenConfiguration()
        configuration.createsNewApplicationInstance = true
        configuration.activates = true
        NSWorkspace.shared.openApplication(
            at: installedApplication.bundleURL,
            configuration: configuration
        ) { _, error in
            if let error {
                logger.error(
                    "openApplication failed for \(installedApplication.displayName): \(error.localizedDescription)"
                )
            }
        }
    }
}
