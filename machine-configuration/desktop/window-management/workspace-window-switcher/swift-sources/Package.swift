// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "WorkspaceWindowSwitcherDaemon",
    platforms: [.macOS(.v14)],
    targets: [
        .executableTarget(
            name: "WorkspaceWindowSwitcherDaemon",
            path: ".",
            exclude: ["__tests__"]
        )
    ]
)
