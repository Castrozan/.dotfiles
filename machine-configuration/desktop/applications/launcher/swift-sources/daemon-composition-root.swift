import AppKit
import Foundation

enum ApplicationLauncherDaemonConfiguration {
    static let commandSocketPath = "/tmp/application-launcher.sock"
    static let socketFileMode: mode_t = 0o600
    static let datagramReadBufferSize = 4096
}

final class ApplicationLauncherDaemonCompositionRoot {
    func bootstrapAndRunForever() {
        NixPackagePathAugmenter.ensureNixPackageDirectoriesArePresentInPathEnvironment()

        let sharedApplication = NSApplication.shared
        sharedApplication.setActivationPolicy(.accessory)
        let applicationDelegate = ApplicationLauncherDaemonApplicationDelegate()
        sharedApplication.delegate = applicationDelegate

        let installedApplicationCatalogCache = InstalledApplicationCatalogCache()
        let launchHistoryStoreCache = LaunchHistoryStoreCache()
        let runningApplicationsRegistryCache = RunningApplicationsRegistryCache()

        installedApplicationCatalogCache.prewarmInBackground()
        launchHistoryStoreCache.prewarm()
        runningApplicationsRegistryCache.prewarmInBackground()

        let showPickerCommandHandler = ShowPickerCommandHandler(
            installedApplicationCatalogCache: installedApplicationCatalogCache,
            launchHistoryStoreCache: launchHistoryStoreCache,
            runningApplicationsRegistryCache: runningApplicationsRegistryCache
        )

        let commandSocketServer = ApplicationLauncherDaemonCommandSocketServer(
            socketPath: ApplicationLauncherDaemonConfiguration.commandSocketPath,
            socketFileMode: ApplicationLauncherDaemonConfiguration.socketFileMode,
            datagramReadBufferSize: ApplicationLauncherDaemonConfiguration.datagramReadBufferSize,
            onCommandReceived: { [weak showPickerCommandHandler] commandString in
                DispatchQueue.main.async {
                    showPickerCommandHandler?.handleSocketCommand(commandString)
                }
            }
        )
        commandSocketServer.startReceivingDatagramsOnBackgroundThread()

        sharedApplication.run()
    }
}
