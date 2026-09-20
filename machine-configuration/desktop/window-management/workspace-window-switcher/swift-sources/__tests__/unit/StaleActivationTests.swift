import Foundation

enum StaleActivationTests {
  static func runAll() {
    cancelledActivationRaisesNoOverlay()
    cancelledActivationLeavesNothingToCommit()
  }

  private static func makeMachine(
    provider: TestWindowProvider,
    overlay: TestOverlay,
    flag: TestActivationFlag,
    timeout: TestCommitTimeout,
    log: URL
  ) -> WindowSwitcherStateMachine {
    WindowSwitcherStateMachine(
      windowProvider: provider, windowFocuser: provider,
      overlayRenderer: overlay, mruTracker: MostRecentlyUsedWindowTracker(),
      activationFlagWriter: flag,
      performanceProfiler: ActivationPerformanceProfiler(logFilePath: log.path),
      commitTimeoutScheduler: timeout, commitTimeoutSeconds: 10)
  }

  private static func pumpMainRunLoopPastTheFetchCallback() {
    let deadline = Date().addingTimeInterval(0.5)
    while Date() < deadline {
      RunLoop.main.run(until: Date().addingTimeInterval(0.002))
    }
  }

  private static func cancelledActivationRaisesNoOverlay() {
    let windows = (1...3).map {
      WorkspaceWindow(identifier: $0, applicationName: "App", title: "Window \($0)")
    }
    let provider = TestWindowProvider(windows: windows)
    let overlay = TestOverlay()
    let flag = TestActivationFlag()
    let timeout = TestCommitTimeout()
    let log = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
    defer { try? FileManager.default.removeItem(at: log) }
    let machine = makeMachine(
      provider: provider, overlay: overlay, flag: flag, timeout: timeout, log: log)

    machine.handleNextCommand()
    precondition(flag.active)
    machine.handleCancelCommand()
    precondition(!flag.active)

    provider.release.signal()
    pumpMainRunLoopPastTheFetchCallback()

    precondition(
      overlay.selections.isEmpty,
      "a fetch that lands after cancel raised an overlay nothing will ever hide")
    precondition(overlay.windows.isEmpty)
  }

  private static func cancelledActivationLeavesNothingToCommit() {
    let windows = [WorkspaceWindow(identifier: 7, applicationName: "App", title: "Window")]
    let provider = TestWindowProvider(windows: windows)
    let overlay = TestOverlay()
    let flag = TestActivationFlag()
    let timeout = TestCommitTimeout()
    let log = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
    defer { try? FileManager.default.removeItem(at: log) }
    let machine = makeMachine(
      provider: provider, overlay: overlay, flag: flag, timeout: timeout, log: log)

    machine.handleNextCommand()
    machine.handleCancelCommand()
    provider.release.signal()
    pumpMainRunLoopPastTheFetchCallback()

    timeout.action?()
    precondition(
      provider.focused.isEmpty,
      "a cancelled activation focused a window through its stale commit timeout")
  }
}
