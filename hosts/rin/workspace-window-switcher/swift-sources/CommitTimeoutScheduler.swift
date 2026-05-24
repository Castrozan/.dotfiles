import Foundation

final class CommitTimeoutTimerScheduler: CommitTimeoutScheduling {
    private var commitTimeoutTimer: Timer?

    func scheduleCommitTimeout(afterSeconds seconds: TimeInterval, onTimeout: @escaping () -> Void) {
        cancelCommitTimeout()
        commitTimeoutTimer = Timer.scheduledTimer(withTimeInterval: seconds, repeats: false) { _ in
            onTimeout()
        }
    }

    func cancelCommitTimeout() {
        commitTimeoutTimer?.invalidate()
        commitTimeoutTimer = nil
    }
}
