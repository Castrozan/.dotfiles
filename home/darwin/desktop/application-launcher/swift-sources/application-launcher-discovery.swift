import Foundation

struct InstalledApplication: Hashable {
    let displayName: String
    let bundleURL: URL
}

struct InstalledApplicationCatalog {
    let applicationsSortedByDisplayName: [InstalledApplication]
    let applicationsByDisplayName: [String: InstalledApplication]

    static let emptyCatalog = InstalledApplicationCatalog(
        applicationsSortedByDisplayName: [],
        applicationsByDisplayName: [:]
    )

    private struct ApplicationSearchDirectory {
        let directoryURL: URL
        let userLaunchableDisplayNameAllowlist: Set<String>?
    }

    private static let coreServicesUserLaunchableDisplayNames: Set<String> = [
        "Finder",
        "Keychain Access",
        "About This Mac",
        "Archive Utility",
        "Directory Utility",
        "Wireless Diagnostics",
        "Feedback Assistant",
        "Screen Time",
        "Software Update",
    ]

    private static let searchDirectories: [ApplicationSearchDirectory] = [
        ApplicationSearchDirectory(
            directoryURL: URL(fileURLWithPath: "/Applications"),
            userLaunchableDisplayNameAllowlist: nil
        ),
        ApplicationSearchDirectory(
            directoryURL: URL(fileURLWithPath: "/Applications/Utilities"),
            userLaunchableDisplayNameAllowlist: nil
        ),
        ApplicationSearchDirectory(
            directoryURL: URL(fileURLWithPath: "/System/Applications"),
            userLaunchableDisplayNameAllowlist: nil
        ),
        ApplicationSearchDirectory(
            directoryURL: URL(fileURLWithPath: "/System/Applications/Utilities"),
            userLaunchableDisplayNameAllowlist: nil
        ),
        ApplicationSearchDirectory(
            directoryURL: FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Applications"),
            userLaunchableDisplayNameAllowlist: nil
        ),
        ApplicationSearchDirectory(
            directoryURL: FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Applications/Home Manager Apps"),
            userLaunchableDisplayNameAllowlist: nil
        ),
        ApplicationSearchDirectory(
            directoryURL: URL(fileURLWithPath: "/System/Library/CoreServices"),
            userLaunchableDisplayNameAllowlist: coreServicesUserLaunchableDisplayNames
        ),
        ApplicationSearchDirectory(
            directoryURL: URL(fileURLWithPath: "/System/Library/CoreServices/Applications"),
            userLaunchableDisplayNameAllowlist: coreServicesUserLaunchableDisplayNames
        ),
    ]

    static func discoverInstalledApplications() -> InstalledApplicationCatalog {
        let fileManager = FileManager.default
        var bundlesByDisplayName: [String: InstalledApplication] = [:]
        for searchDirectory in searchDirectories {
            guard let directoryContents = try? fileManager.contentsOfDirectory(
                at: searchDirectory.directoryURL,
                includingPropertiesForKeys: nil
            ) else { continue }
            for bundleURL in directoryContents where bundleURL.pathExtension == "app" {
                let displayName = bundleURL.deletingPathExtension().lastPathComponent
                if let allowlist = searchDirectory.userLaunchableDisplayNameAllowlist,
                    !allowlist.contains(displayName)
                {
                    continue
                }
                bundlesByDisplayName[displayName] = InstalledApplication(
                    displayName: displayName,
                    bundleURL: bundleURL
                )
            }
        }
        return InstalledApplicationCatalog(
            applicationsSortedByDisplayName: bundlesByDisplayName.values.sorted { $0.displayName < $1.displayName },
            applicationsByDisplayName: bundlesByDisplayName
        )
    }

    func application(named displayName: String) -> InstalledApplication? {
        return applicationsByDisplayName[displayName]
    }
}

enum NixPackagePathAugmenter {
    private static let candidateNixPackageDirectories: [String] = {
        let currentUserName = ProcessInfo.processInfo.environment["USER"] ?? "nobody"
        return [
            FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent(".nix-profile/bin").path,
            "/run/current-system/sw/bin",
            "/etc/profiles/per-user/\(currentUserName)/bin",
        ]
    }()

    static func ensureNixPackageDirectoriesArePresentInPathEnvironment() {
        let fileManager = FileManager.default
        let existingPathEnvironment = ProcessInfo.processInfo.environment["PATH"] ?? ""
        let presentNixPackageDirectories = candidateNixPackageDirectories.filter { directoryPath in
            var isDirectory: ObjCBool = false
            return fileManager.fileExists(atPath: directoryPath, isDirectory: &isDirectory)
                && isDirectory.boolValue
        }
        let augmentedPathEnvironment = (presentNixPackageDirectories + [existingPathEnvironment])
            .joined(separator: ":")
        setenv("PATH", augmentedPathEnvironment, 1)
    }
}
