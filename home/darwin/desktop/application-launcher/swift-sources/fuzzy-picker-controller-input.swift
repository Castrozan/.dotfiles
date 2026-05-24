import Cocoa

extension FuzzyPickerController {
    func controlTextDidChange(_ notification: Notification) {
        let query = searchField.stringValue
        if query.isEmpty {
            filteredItems = allItems
        } else {
            filteredItems = allItems.filter { fuzzyMatch(item: $0, query: query) }
        }
        tableView.reloadData()
        if !filteredItems.isEmpty {
            tableView.selectRowIndexes(IndexSet(integer: 0), byExtendingSelection: false)
            tableView.scrollRowToVisible(0)
        }
    }

    func control(_ control: NSControl, textView: NSTextView, doCommandBy commandSelector: Selector) -> Bool {
        if commandSelector == #selector(NSResponder.insertNewline(_:)) {
            commitSelection()
            return true
        }
        if commandSelector == #selector(NSResponder.cancelOperation(_:)) {
            dismissWithoutSelection()
            return true
        }
        if commandSelector == #selector(NSResponder.moveDown(_:)) {
            let nextRow = min(tableView.selectedRow + 1, filteredItems.count - 1)
            tableView.selectRowIndexes(IndexSet(integer: nextRow), byExtendingSelection: false)
            tableView.scrollRowToVisible(nextRow)
            return true
        }
        if commandSelector == #selector(NSResponder.moveUp(_:)) {
            let prevRow = max(tableView.selectedRow - 1, 0)
            tableView.selectRowIndexes(IndexSet(integer: prevRow), byExtendingSelection: false)
            tableView.scrollRowToVisible(prevRow)
            return true
        }
        return false
    }
}
