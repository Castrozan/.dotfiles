import Foundation

final class LaunchHistoryStoreCache {
    private let lock = NSLock()
    private var cachedStore: LaunchHistoryStore?

    func prewarm() {
        let freshStore = LaunchHistoryStore.loadOrEmpty()
        lock.lock()
        cachedStore = freshStore
        lock.unlock()
    }

    func currentStoreOrFreshlyLoadedFromDisk() -> LaunchHistoryStore {
        lock.lock()
        if let cached = cachedStore {
            lock.unlock()
            return cached
        }
        lock.unlock()
        let freshStore = LaunchHistoryStore.loadOrEmpty()
        lock.lock()
        cachedStore = freshStore
        lock.unlock()
        return freshStore
    }

    func updateCachedStore(_ newStore: LaunchHistoryStore) {
        lock.lock()
        cachedStore = newStore
        lock.unlock()
    }
}
