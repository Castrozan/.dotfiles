import Foundation

final class InstalledApplicationCatalogCache {
    private let lock = NSLock()
    private var cachedCatalog: InstalledApplicationCatalog?
    private var refreshInProgress = false

    func prewarmInBackground() {
        DispatchQueue.global(qos: .userInitiated).async { [weak self] in
            let freshCatalog = InstalledApplicationCatalog.discoverInstalledApplications()
            self?.lock.lock()
            self?.cachedCatalog = freshCatalog
            self?.lock.unlock()
        }
    }

    func currentCatalogOrEmpty() -> InstalledApplicationCatalog {
        lock.lock()
        let snapshot = cachedCatalog
        lock.unlock()
        return snapshot ?? InstalledApplicationCatalog.emptyCatalog
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
            let freshCatalog = InstalledApplicationCatalog.discoverInstalledApplications()
            self?.lock.lock()
            self?.cachedCatalog = freshCatalog
            self?.refreshInProgress = false
            self?.lock.unlock()
        }
    }
}
