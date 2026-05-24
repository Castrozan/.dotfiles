import Cocoa

class FuzzyPickerController: NSObject,
    NSTextFieldDelegate,
    NSTableViewDataSource,
    NSTableViewDelegate,
    NSWindowDelegate
{
    let allItems: [String]
    var filteredItems: [String]
    let tableView: NSTableView
    let searchField: NSTextField
    let window: NSPanel
    var selectedResult: String?

    private let onDismissedWithSelection: (String) -> Void
    private let onDismissedWithoutSelection: () -> Void
    private var hasNotifiedDismissalObservers = false

    init(
        items: [String],
        onDismissedWithSelection: @escaping (String) -> Void,
        onDismissedWithoutSelection: @escaping () -> Void
    ) {
        self.allItems = items
        self.filteredItems = items
        self.onDismissedWithSelection = onDismissedWithSelection
        self.onDismissedWithoutSelection = onDismissedWithoutSelection

        let windowWidth: CGFloat = 600
        let windowHeight: CGFloat = 400
        let screenFrame = NSScreen.main?.visibleFrame ?? NSRect(x: 0, y: 0, width: 1920, height: 1080)
        let windowOriginX = screenFrame.midX - windowWidth / 2
        let windowOriginY = screenFrame.midY - windowHeight / 2 + screenFrame.height * 0.15
        let windowFrame = NSRect(x: windowOriginX, y: windowOriginY, width: windowWidth, height: windowHeight)

        window = NSPanel(
            contentRect: windowFrame,
            styleMask: [.titled, .nonactivatingPanel, .fullSizeContentView],
            backing: .buffered,
            defer: true
        )
        window.titlebarAppearsTransparent = true
        window.titleVisibility = .hidden
        window.isMovableByWindowBackground = true
        window.level = .floating
        window.isOpaque = false
        window.backgroundColor = NSColor(white: 0.13, alpha: 0.95)
        window.hasShadow = true

        searchField = NSTextField(frame: NSRect(x: 16, y: 0, width: Int(windowWidth) - 32, height: 28))
        searchField.placeholderString = "Search applications..."
        searchField.font = NSFont.systemFont(ofSize: 18)
        searchField.focusRingType = .none
        searchField.isBezeled = false
        searchField.drawsBackground = false
        searchField.textColor = .white

        let scrollView = NSScrollView(frame: NSRect(x: 0, y: 0, width: Int(windowWidth), height: Int(windowHeight) - 50))
        scrollView.hasVerticalScroller = true
        scrollView.drawsBackground = false
        scrollView.borderType = .noBorder

        tableView = NSTableView(frame: .zero)
        tableView.headerView = nil
        tableView.backgroundColor = .clear
        tableView.selectionHighlightStyle = .regular
        tableView.rowHeight = 30
        tableView.intercellSpacing = NSSize(width: 0, height: 1)

        let column = NSTableColumn(identifier: NSUserInterfaceItemIdentifier("item"))
        column.isEditable = false
        tableView.addTableColumn(column)
        scrollView.documentView = tableView

        let contentView = window.contentView!
        searchField.frame = NSRect(x: 16, y: Int(windowHeight) - 40, width: Int(windowWidth) - 32, height: 28)
        scrollView.frame = NSRect(x: 0, y: 0, width: Int(windowWidth), height: Int(windowHeight) - 48)
        contentView.addSubview(searchField)
        contentView.addSubview(scrollView)

        super.init()

        searchField.delegate = self
        tableView.dataSource = self
        tableView.delegate = self
        window.delegate = self
    }

    func show() {
        window.makeKeyAndOrderFront(nil)
        window.makeFirstResponder(searchField)
        NSApp.activate(ignoringOtherApps: true)
        if !filteredItems.isEmpty {
            tableView.selectRowIndexes(IndexSet(integer: 0), byExtendingSelection: false)
        }
    }

    func hide() {
        window.orderOut(nil)
    }

    func commitSelection() {
        let row = tableView.selectedRow
        if row >= 0 && row < filteredItems.count {
            selectedResult = filteredItems[row]
        }
        notifyDismissalObserversOnce()
    }

    func dismissWithoutSelection() {
        selectedResult = nil
        notifyDismissalObserversOnce()
    }

    func windowDidResignKey(_ notification: Notification) {
        dismissWithoutSelection()
    }

    func tableViewSelectionDidChange(_ notification: Notification) {}

    private func notifyDismissalObserversOnce() {
        guard !hasNotifiedDismissalObservers else { return }
        hasNotifiedDismissalObservers = true
        if let selectedResult {
            onDismissedWithSelection(selectedResult)
        } else {
            onDismissedWithoutSelection()
        }
    }
}
