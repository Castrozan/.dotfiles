import AppKit
import Foundation

final class ShowPickerCommandHandler {
    private let installedApplicationCatalogCache: InstalledApplicationCatalogCache
    private let launchHistoryStoreCache: LaunchHistoryStoreCache
    private let runningApplicationsRegistryCache: RunningApplicationsRegistryCache
    private var currentlyShowingPickerController: FuzzyPickerController?
    private var previouslyFrontmostApplicationBeforePickerShown: NSRunningApplication?

    init(
        installedApplicationCatalogCache: InstalledApplicationCatalogCache,
        launchHistoryStoreCache: LaunchHistoryStoreCache,
        runningApplicationsRegistryCache: RunningApplicationsRegistryCache
    ) {
        self.installedApplicationCatalogCache = installedApplicationCatalogCache
        self.launchHistoryStoreCache = launchHistoryStoreCache
        self.runningApplicationsRegistryCache = runningApplicationsRegistryCache
    }

    func handleSocketCommand(_ rawCommand: String) {
        let parsedCommand = SocketCommandParser.parse(rawCommand)
        switch parsedCommand {
        case .showPicker(let perRequestProfileOutputFilePath):
            showPicker(perRequestProfileOutputFilePath: perRequestProfileOutputFilePath)
        case .dumpDisplayLinesToFile(let outputFilePath):
            dumpDisplayLinesToFile(outputFilePath)
        case .dismissPicker:
            currentlyShowingPickerController?.dismissWithoutSelection()
            currentlyShowingPickerController = nil
        case .unknown:
            return
        }
    }

    private func showPicker(perRequestProfileOutputFilePath: String?) {
        let socketCommandReceivedAtNanoseconds = DispatchTime.now().uptimeNanoseconds
        let perRequestProfiler = perRequestProfileOutputFilePath.map {
            PerRequestColdStartProfiler(
                outputFilePath: $0,
                baselineNanoseconds: socketCommandReceivedAtNanoseconds
            )
        }
        perRequestProfiler?.recordMilestone("socket command received")

        if currentlyShowingPickerController != nil {
            currentlyShowingPickerController?.dismissWithoutSelection()
            return
        }

        previouslyFrontmostApplicationBeforePickerShown = NSWorkspace.shared.frontmostApplication

        let installedApplicationCatalog = installedApplicationCatalogCache.currentCatalogOrEmpty()
        let launchHistoryStore = launchHistoryStoreCache.currentStoreOrFreshlyLoadedFromDisk()
        let runningApplicationsRegistry = runningApplicationsRegistryCache.currentRegistryOrEmpty()
        perRequestProfiler?.recordMilestone("caches read + running apps queried")

        let displayNamesSortedByFrecency = launchHistoryStore.sortApplicationNamesByFrecency(
            installedApplicationCatalog.applicationsSortedByDisplayName.map(\.displayName)
        )
        let displayLines = displayNamesSortedByFrecency.map {
            runningApplicationsRegistry.buildDisplayLine(forApplicationNamed: $0)
        }
        let displayLineToApplicationName = Dictionary(
            uniqueKeysWithValues: zip(displayLines, displayNamesSortedByFrecency)
        )
        perRequestProfiler?.recordMilestone("display lines built (count=\(displayLines.count))")

        if displayLines.isEmpty {
            installedApplicationCatalogCache.refreshInBackground()
            return
        }

        let newPickerController = FuzzyPickerController(
            items: displayLines,
            onDismissedWithSelection: { [weak self] selectedDisplayLine in
                self?.handleSelection(
                    selectedDisplayLine: selectedDisplayLine,
                    displayLineToApplicationName: displayLineToApplicationName,
                    installedApplicationCatalog: installedApplicationCatalog,
                    launchHistoryStore: launchHistoryStore
                )
            },
            onDismissedWithoutSelection: { [weak self] in
                self?.disposeCurrentlyShowingController()
            }
        )
        newPickerController.show()
        currentlyShowingPickerController = newPickerController
        perRequestProfiler?.recordMilestone("picker visible")

        installedApplicationCatalogCache.refreshInBackground()
        runningApplicationsRegistryCache.refreshInBackground()
    }

    private func handleSelection(
        selectedDisplayLine: String,
        displayLineToApplicationName: [String: String],
        installedApplicationCatalog: InstalledApplicationCatalog,
        launchHistoryStore: LaunchHistoryStore
    ) {
        let selectedApplicationName = displayLineToApplicationName[selectedDisplayLine]
            ?? RunningApplicationsRegistry.extractApplicationName(fromDisplayLine: selectedDisplayLine)
        var mutableLaunchHistoryStore = launchHistoryStore
        mutableLaunchHistoryStore.recordLaunchOfApplication(named: selectedApplicationName)
        launchHistoryStoreCache.updateCachedStore(mutableLaunchHistoryStore)
        if let installedApplication = installedApplicationCatalog
            .application(named: selectedApplicationName)
        {
            ApplicationLaunchAction.launchApplication(installedApplication)
        }
        disposeCurrentlyShowingController()
    }

    private func disposeCurrentlyShowingController() {
        currentlyShowingPickerController?.hide()
        currentlyShowingPickerController = nil
        restoreFocusToApplicationFrontmostBeforePickerShown()
    }

    private func restoreFocusToApplicationFrontmostBeforePickerShown() {
        guard let previousApplication = previouslyFrontmostApplicationBeforePickerShown else { return }
        previouslyFrontmostApplicationBeforePickerShown = nil
        if previousApplication.bundleIdentifier == Bundle.main.bundleIdentifier { return }
        previousApplication.activate(options: [])
    }

    private func dumpDisplayLinesToFile(_ outputFilePath: String) {
        let installedApplicationCatalog = installedApplicationCatalogCache.currentCatalogOrEmpty()
        let launchHistoryStore = launchHistoryStoreCache.currentStoreOrFreshlyLoadedFromDisk()
        let runningApplicationsRegistry = runningApplicationsRegistryCache.currentRegistryOrEmpty()
        let displayNamesSortedByFrecency = launchHistoryStore.sortApplicationNamesByFrecency(
            installedApplicationCatalog.applicationsSortedByDisplayName.map(\.displayName)
        )
        let displayLines = displayNamesSortedByFrecency.map {
            runningApplicationsRegistry.buildDisplayLine(forApplicationNamed: $0)
        }
        let fileContents = displayLines.joined(separator: "\n") + "\n"
        try? fileContents.write(toFile: outputFilePath, atomically: true, encoding: .utf8)
    }
}

