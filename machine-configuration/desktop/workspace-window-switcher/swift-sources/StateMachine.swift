import Foundation

final class WindowSwitcherStateMachine: SocketCommandHandling {
    private let windowProvider: WindowProviding
    private let windowFocuser: WindowFocusing
    private let overlayRenderer: OverlayRendering
    private let mruTracker: MruTracking
    private let activationFlagWriter: ActivationFlagWriting
    private let performanceProfiler: PerformanceProfiling
    private let commitTimeoutScheduler: CommitTimeoutScheduling
    private let commitTimeoutSeconds: TimeInterval

    private var orderedWindows: [WorkspaceWindow] = []
    private var selectedWindowIndex: Int = 0
    private var isActivationActive: Bool = false
    private var isFetchingWindows: Bool = false
    private var commitRequestedBeforeFetchCompleted: Bool = false
    private var accumulatedPendingDirectionChanges: Int = 0

    init(
        windowProvider: WindowProviding,
        windowFocuser: WindowFocusing,
        overlayRenderer: OverlayRendering,
        mruTracker: MruTracking,
        activationFlagWriter: ActivationFlagWriting,
        performanceProfiler: PerformanceProfiling,
        commitTimeoutScheduler: CommitTimeoutScheduling,
        commitTimeoutSeconds: TimeInterval
    ) {
        self.windowProvider = windowProvider
        self.windowFocuser = windowFocuser
        self.overlayRenderer = overlayRenderer
        self.mruTracker = mruTracker
        self.activationFlagWriter = activationFlagWriter
        self.performanceProfiler = performanceProfiler
        self.commitTimeoutScheduler = commitTimeoutScheduler
        self.commitTimeoutSeconds = commitTimeoutSeconds
    }

    func handleNextCommand() {
        if !isActivationActive {
            beginActivation(withInitialDirection: 1)
            return
        }
        if isFetchingWindows {
            accumulatedPendingDirectionChanges += 1
            return
        }
        advanceSelection(by: 1)
        rescheduleCommitTimeout()
    }

    func handlePrevCommand() {
        if !isActivationActive {
            beginActivation(withInitialDirection: -1)
            return
        }
        if isFetchingWindows {
            accumulatedPendingDirectionChanges -= 1
            return
        }
        advanceSelection(by: -1)
        rescheduleCommitTimeout()
    }

    func handleCommitCommand() {
        if !isActivationActive { return }
        if isFetchingWindows {
            commitRequestedBeforeFetchCompleted = true
            return
        }
        commitTimeoutScheduler.cancelCommitTimeout()
        focusSelectedWindowAndDeactivate()
    }

    func handleCancelCommand() {
        commitTimeoutScheduler.cancelCommitTimeout()
        deactivate()
    }

    func recordExternallyFocusedWindow(_ windowIdentifier: Int) {
        mruTracker.recordFocusedWindow(windowIdentifier)
    }

    private func beginActivation(withInitialDirection initialDirection: Int) {
        performanceProfiler.beginNewActivation()
        isActivationActive = true
        activationFlagWriter.writeActivationFlag()
        isFetchingWindows = true
        commitRequestedBeforeFetchCompleted = false
        accumulatedPendingDirectionChanges = initialDirection
        DispatchQueue.global(qos: .userInteractive).async { [weak self] in
            self?.fetchWindowsFromProviderOnBackgroundThread()
        }
    }

    private func fetchWindowsFromProviderOnBackgroundThread() {
        performanceProfiler.markPhase("worker_started")
        let workspaceWindows = windowProvider.getFocusedWorkspaceWindows()
        performanceProfiler.markPhase("ipc_workspace_done")
        let focusedWindowIdentifier = windowProvider.getFocusedWindowIdentifier()
        performanceProfiler.markPhase("ipc_focus_done")
        DispatchQueue.main.async { [weak self] in
            self?.onWindowsFetched(
                workspaceWindows: workspaceWindows,
                focusedWindowIdentifier: focusedWindowIdentifier
            )
        }
    }

    private func onWindowsFetched(workspaceWindows: [WorkspaceWindow], focusedWindowIdentifier: Int?) {
        performanceProfiler.markPhase("main_callback")
        performanceProfiler.recordWorkspaceWindowCount(workspaceWindows.count)
        isFetchingWindows = false

        if workspaceWindows.isEmpty {
            deactivate()
            return
        }

        let currentWindowIdentifiers = Set(workspaceWindows.map { $0.identifier })
        mruTracker.removeStaleWindowIdentifiers(currentWindowIdentifiers: currentWindowIdentifiers)
        if let focusedIdentifier = focusedWindowIdentifier {
            mruTracker.recordFocusedWindow(focusedIdentifier)
        }
        orderedWindows = mruTracker.sortWindowsByRecency(workspaceWindows)
        performanceProfiler.markPhase("mru_sort_done")

        selectedWindowIndex = SelectionIndexCalculator.initialIndexFromAccumulatedDirection(
            accumulatedPendingDirectionChanges,
            totalCount: orderedWindows.count
        )

        if commitRequestedBeforeFetchCompleted {
            focusSelectedWindowAndDeactivate()
            return
        }

        overlayRenderer.showWithWindowsAndSelection(orderedWindows, selectedIndex: selectedWindowIndex)
        performanceProfiler.markPhase("overlay_visible")
        performanceProfiler.emitActivationReport()
        rescheduleCommitTimeout()
    }

    private func advanceSelection(by direction: Int) {
        if orderedWindows.isEmpty { return }
        selectedWindowIndex = SelectionIndexCalculator.cycledIndex(
            currentValue: selectedWindowIndex,
            direction: direction,
            totalCount: orderedWindows.count
        )
        overlayRenderer.updateSelectedIndex(selectedWindowIndex)
    }

    private func focusSelectedWindowAndDeactivate() {
        if !orderedWindows.isEmpty,
            selectedWindowIndex >= 0,
            selectedWindowIndex < orderedWindows.count
        {
            windowFocuser.focusWindow(withIdentifier: orderedWindows[selectedWindowIndex].identifier)
        }
        deactivate()
    }

    private func deactivate() {
        commitTimeoutScheduler.cancelCommitTimeout()
        activationFlagWriter.clearActivationFlag()
        isActivationActive = false
        isFetchingWindows = false
        commitRequestedBeforeFetchCompleted = false
        accumulatedPendingDirectionChanges = 0
        orderedWindows = []
        selectedWindowIndex = 0
        overlayRenderer.hide()
    }

    private func rescheduleCommitTimeout() {
        commitTimeoutScheduler.cancelCommitTimeout()
        commitTimeoutScheduler.scheduleCommitTimeout(afterSeconds: commitTimeoutSeconds) { [weak self] in
            self?.handleCommitCommand()
        }
    }
}
