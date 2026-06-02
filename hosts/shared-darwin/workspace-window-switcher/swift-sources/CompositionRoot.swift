import AppKit
import Foundation

final class DaemonCompositionRoot {
    func bootstrapAndRun() {
        try? FileManager.default.removeItem(atPath: DaemonConfiguration.activationFlagFilePath)

        let application = NSApplication.shared
        application.setActivationPolicy(.accessory)

        let composedDependencies = buildAllDependencies()
        composedDependencies.applicationIconProvider.prewarmCacheFromRunningApplications()
        composedDependencies.commandSocketServer.startReceivingDatagramsOnBackgroundThread()

        application.run()
    }

    private func buildAllDependencies() -> ComposedDaemonDependencies {
        let aerospaceSocketPathResolver = AeroSpaceSocketPathResolver()
        let aerospaceIpcClient = AeroSpaceIpcClient(
            socketPathResolver: aerospaceSocketPathResolver,
            connectionTimeoutSeconds: DaemonConfiguration.aerospaceIpcTimeoutSeconds
        )
        let aerospaceWindowProvider = AeroSpaceWindowProvider(ipcClient: aerospaceIpcClient)

        let applicationIconProvider = ApplicationIconProvider()
        let activationPerformanceProfiler = ActivationPerformanceProfiler(
            logFilePath: DaemonConfiguration.performanceLogFilePath
        )
        let mostRecentlyUsedWindowTracker = MostRecentlyUsedWindowTracker()
        let activationFlagFileWriter = ActivationFlagFileWriter(
            flagFilePath: DaemonConfiguration.activationFlagFilePath
        )
        let commitTimeoutTimerScheduler = CommitTimeoutTimerScheduler()

        let windowCardViewFactory = WindowCardViewFactory(
            iconProvider: applicationIconProvider,
            cardWidth: DaemonConfiguration.cardWidth,
            cardHeight: DaemonConfiguration.cardHeight,
            cardIconSize: DaemonConfiguration.cardIconSize,
            cardCornerRadius: DaemonConfiguration.cardCornerRadius,
            selectionBorderWidth: DaemonConfiguration.selectionBorderWidth,
            cardIconTopPadding: DaemonConfiguration.cardIconTopPadding,
            cardTitleHorizontalInset: DaemonConfiguration.cardTitleHorizontalInset,
            cardTitleBottomOffset: DaemonConfiguration.cardTitleBottomOffset,
            cardTitleHeight: DaemonConfiguration.cardTitleHeight
        )
        let cardSelectionStyler = CardSelectionStyler(titleFontSize: DaemonConfiguration.titleFontSize)
        let switcherOverlayPanel = SwitcherOverlayPanel(
            cardViewFactory: windowCardViewFactory,
            selectionStyler: cardSelectionStyler,
            cardWidth: DaemonConfiguration.cardWidth,
            cardHeight: DaemonConfiguration.cardHeight,
            cardSpacing: DaemonConfiguration.cardSpacing,
            overlayPadding: DaemonConfiguration.overlayPadding,
            overlayCornerRadius: DaemonConfiguration.overlayCornerRadius
        )

        let windowSwitcherStateMachine = WindowSwitcherStateMachine(
            windowProvider: aerospaceWindowProvider,
            windowFocuser: aerospaceWindowProvider,
            overlayRenderer: switcherOverlayPanel,
            mruTracker: mostRecentlyUsedWindowTracker,
            activationFlagWriter: activationFlagFileWriter,
            performanceProfiler: activationPerformanceProfiler,
            commitTimeoutScheduler: commitTimeoutTimerScheduler,
            commitTimeoutSeconds: DaemonConfiguration.commitTimeoutSeconds
        )

        let socketCommandMainThreadDispatcher = SocketCommandMainThreadDispatcher(
            commandHandler: windowSwitcherStateMachine
        )
        let commandSocketServer = CommandSocketServer(
            socketPath: DaemonConfiguration.commandSocketPath,
            socketFileMode: DaemonConfiguration.commandSocketFileMode,
            datagramReadBufferSize: DaemonConfiguration.datagramReadBufferSize,
            kernelReceiveBufferBytes: DaemonConfiguration.kernelReceiveBufferBytes,
            onCommandReceived: { trimmedCommandString in
                guard let parsedCommand = SocketCommandParser.parseTrimmedCommand(trimmedCommandString) else {
                    return
                }
                socketCommandMainThreadDispatcher.dispatchOnMainThread(parsedCommand)
            }
        )

        return ComposedDaemonDependencies(
            applicationIconProvider: applicationIconProvider,
            commandSocketServer: commandSocketServer
        )
    }
}

private struct ComposedDaemonDependencies {
    let applicationIconProvider: IconProviding
    let commandSocketServer: CommandSocketServer
}
