import Foundation

final class RunningApplicationsRegistryCache {
    private let lock = NSLock()
    private var cachedRegistry: RunningApplicationsRegistry?
    private var refreshInProgress = false

    func prewarmInBackground() {
        DispatchQueue.global(qos: .userInitiated).async { [weak self] in
            let freshRegistry = RunningApplicationsRegistry.snapshotCurrent()
            self?.lock.lock()
            self?.cachedRegistry = freshRegistry
            self?.lock.unlock()
        }
    }

    func currentRegistryOrEmpty() -> RunningApplicationsRegistry {
        lock.lock()
        let snapshot = cachedRegistry
        lock.unlock()
        return snapshot ?? RunningApplicationsRegistry(applicationNames: [])
    }

    func refreshInBackground() {
        lock.lock()
        if refreshInProgress {
            lock.unlock()
            return
        }
        refreshInProgress = true
        lock.unlock()

        DispatchQueue.global(qos: .background).async { [weak self] in
            let freshRegistry = RunningApplicationsRegistry.snapshotCurrent()
            self?.lock.lock()
            self?.cachedRegistry = freshRegistry
            self?.refreshInProgress = false
            self?.lock.unlock()
        }
    }
}
