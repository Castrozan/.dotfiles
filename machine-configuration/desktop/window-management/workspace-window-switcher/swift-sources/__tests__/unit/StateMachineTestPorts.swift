import Foundation

final class TestWindowProvider: WindowProviding, WindowFocusing {
  let release = DispatchSemaphore(value: 0)
  let windows: [WorkspaceWindow]
  var focused: [Int] = []
  init(windows: [WorkspaceWindow]) { self.windows = windows }
  func getFocusedWorkspaceWindows() -> [WorkspaceWindow] {
    precondition(release.wait(timeout: .now() + 3) == .success)
    return windows
  }
  func getFocusedWindowIdentifier() -> Int? { windows.first?.identifier }
  func focusWindow(withIdentifier identifier: Int) { focused.append(identifier) }
}

final class TestOverlay: OverlayRendering {
  var windows: [WorkspaceWindow] = []
  var selections: [Int] = []
  var hides = 0
  func showWithWindowsAndSelection(_ windows: [WorkspaceWindow], selectedIndex: Int) {
    self.windows = windows
    selections.append(selectedIndex)
  }
  func updateSelectedIndex(_ selectedIndex: Int) { selections.append(selectedIndex) }
  func hide() { hides += 1 }
}

final class TestActivationFlag: ActivationFlagWriting {
  var active = false
  func writeActivationFlag() { active = true }
  func clearActivationFlag() { active = false }
}

final class TestCommitTimeout: CommitTimeoutScheduling {
  var seconds: TimeInterval?
  var action: (() -> Void)?
  func scheduleCommitTimeout(afterSeconds seconds: TimeInterval, onTimeout: @escaping () -> Void) {
    self.seconds = seconds
    action = onTimeout
  }
  func cancelCommitTimeout() { action = nil }
}

enum TestMainRunLoop {
  static func until(_ predicate: () -> Bool) {
    let deadline = Date().addingTimeInterval(3)
    while !predicate() && Date() < deadline {
      RunLoop.main.run(until: Date().addingTimeInterval(0.002))
    }
    precondition(predicate(), "Main-thread callback timed out")
  }
}
