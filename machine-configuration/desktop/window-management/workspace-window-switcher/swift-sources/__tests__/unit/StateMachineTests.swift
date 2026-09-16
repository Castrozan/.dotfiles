import Foundation

enum StateMachineTests {
  static func runAll() {
    for scenario in ["cycle", "early-commit", "timeout", "cancel", "empty", "previous"] {
      let windows =
        scenario == "empty"
        ? []
        : (1...3).map {
          WorkspaceWindow(identifier: $0, applicationName: "App", title: "Window \($0)")
        }
      let provider = TestWindowProvider(windows: windows)
      let overlay = TestOverlay()
      let flag = TestActivationFlag()
      let timeout = TestCommitTimeout()
      let log = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
      defer { try? FileManager.default.removeItem(at: log) }
      let machine = WindowSwitcherStateMachine(
        windowProvider: provider, windowFocuser: provider,
        overlayRenderer: overlay, mruTracker: MostRecentlyUsedWindowTracker(),
        activationFlagWriter: flag,
        performanceProfiler: ActivationPerformanceProfiler(logFilePath: log.path),
        commitTimeoutScheduler: timeout, commitTimeoutSeconds: 10)
      machine.handleCommitCommand()
      precondition(provider.focused.isEmpty)
      machine.recordExternallyFocusedWindow(2)
      if scenario == "previous" { machine.handlePrevCommand() } else { machine.handleNextCommand() }
      precondition(flag.active)
      if scenario == "early-commit" {
        machine.handleNextCommand()
        machine.handlePrevCommand()
        machine.handleCommitCommand()
      }
      provider.release.signal()
      TestMainRunLoop.until { !overlay.selections.isEmpty || overlay.hides > 0 }
      if scenario == "empty" {
        precondition(!flag.active && overlay.windows.isEmpty && provider.focused.isEmpty)
        continue
      }
      if scenario == "early-commit" {
        precondition(provider.focused == [2] && overlay.selections.isEmpty && !flag.active)
        continue
      }
      precondition(overlay.windows.map(\.identifier) == [1, 2, 3])
      precondition(overlay.selections == [scenario == "previous" ? 2 : 1])
      precondition(timeout.seconds == 10 && timeout.action != nil)
      switch scenario {
      case "cycle":
        machine.handleNextCommand()
        machine.handleNextCommand()
        machine.handlePrevCommand()
        precondition(overlay.selections == [1, 2, 0, 2])
        machine.handleCommitCommand()
        precondition(provider.focused == [3])
      case "timeout":
        timeout.action?()
        precondition(provider.focused == [2])
      case "previous":
        machine.handleCommitCommand()
        precondition(provider.focused == [3])
      default:
        machine.handleCancelCommand()
        precondition(provider.focused.isEmpty)
      }
      precondition(!flag.active && timeout.action == nil && overlay.hides == 1)
      machine.handleCommitCommand()
      precondition(overlay.hides == 1)
    }
  }
}
