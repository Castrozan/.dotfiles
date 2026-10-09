// swift-tools-version:5.9
import PackageDescription

let package = Package(
  name: "DesktopDaemons",
  platforms: [.macOS(.v14)],
  products: [
    .executable(name: "ApplicationLauncherDaemon", targets: ["ApplicationLauncherDaemon"]),
    .executable(name: "WorkspaceWindowSwitcherDaemon", targets: ["WorkspaceWindowSwitcherDaemon"]),
  ],
  targets: [
    .target(name: "DesktopCommandSockets", path: "input/command-sockets/swift-sources"),
    .executableTarget(
      name: "ApplicationLauncherDaemon",
      dependencies: ["DesktopCommandSockets"],
      path: "applications/launcher/swift-sources",
      exclude: ["__tests__"]
    ),
    .executableTarget(
      name: "WorkspaceWindowSwitcherDaemon",
      dependencies: ["DesktopCommandSockets"],
      path: "window-management/workspace-window-switcher/swift-sources",
      exclude: ["__tests__"]
    ),
  ]
)
