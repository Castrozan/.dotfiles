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

    private static let searchDirectories: [URL] = [
        URL(fileURLWithPath: "/Applications"),
        URL(fileURLWithPath: "/Applications/Utilities"),
        URL(fileURLWithPath: "/System/Applications"),
        URL(fileURLWithPath: "/System/Applications/Utilities"),
        FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Applications"),
        FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Applications/Home Manager Apps"),
    ]

    static func discoverInstalledApplications() -> InstalledApplicationCatalog {
        let fileManager = FileManager.default
        var bundlesByDisplayName: [String: InstalledApplication] = [:]
        for searchDirectory in searchDirectories {
            guard let directoryContents = try? fileManager.contentsOfDirectory(
                at: searchDirectory,
                includingPropertiesForKeys: nil
            ) else { continue }
            for bundleURL in directoryContents where bundleURL.pathExtension == "app" {
                let displayName = bundleURL.deletingPathExtension().lastPathComponent
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
