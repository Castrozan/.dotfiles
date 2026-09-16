import AppKit

enum PickerTests {
  static func runAll() {
    var selections: [String] = []
    var cancellations = 0
    let picker = FuzzyPickerController(
      items: ["Terminal", "Visual Studio Code", "Browser"],
      onDismissedWithSelection: { selections.append($0) },
      onDismissedWithoutSelection: { cancellations += 1 })
    precondition(picker.window.frame.size == NSSize(width: 600, height: 400))
    let notification = Notification(name: NSControl.textDidChangeNotification)
    picker.searchField.stringValue = "vsc"
    picker.controlTextDidChange(notification)
    precondition(picker.filteredItems == ["Visual Studio Code"])
    precondition(picker.tableView.selectedRow == 0)
    precondition(picker.numberOfRows(in: picker.tableView) == 1)
    let cell = picker.tableView(picker.tableView, viewFor: nil, row: 0) as! NSTableCellView
    precondition(cell.textField?.stringValue == "Visual Studio Code")
    precondition(picker.tableView(picker.tableView, rowViewForRow: 0) is PickerRowView)
    picker.searchField.stringValue = "no matching application"
    picker.controlTextDidChange(notification)
    precondition(picker.filteredItems.isEmpty)
    picker.searchField.stringValue = ""
    picker.controlTextDidChange(notification)
    precondition(picker.filteredItems == picker.allItems)
    let editor = NSTextView()
    func send(_ selector: Selector) -> Bool {
      picker.control(picker.searchField, textView: editor, doCommandBy: selector)
    }
    for _ in 0..<5 { precondition(send(#selector(NSResponder.moveDown(_:)))) }
    precondition(picker.tableView.selectedRow == 2)
    for _ in 0..<5 { precondition(send(#selector(NSResponder.moveUp(_:)))) }
    precondition(picker.tableView.selectedRow == 0)
    precondition(!send(#selector(NSResponder.moveLeft(_:))))
    precondition(send(#selector(NSResponder.insertNewline(_:))))
    picker.commitSelection()
    picker.dismissWithoutSelection()
    precondition(selections == ["Terminal"] && cancellations == 0)
    picker.hide()
    precondition(!picker.window.isVisible)
    let empty = FuzzyPickerController(
      items: [], onDismissedWithSelection: { _ in preconditionFailure() },
      onDismissedWithoutSelection: { cancellations += 1 })
    empty.commitSelection()
    empty.windowDidResignKey(Notification(name: NSWindow.didResignKeyNotification))
    precondition(cancellations == 1)
    let cancelled = FuzzyPickerController(
      items: ["Browser"], onDismissedWithSelection: { _ in preconditionFailure() },
      onDismissedWithoutSelection: { cancellations += 1 })
    precondition(
      cancelled.control(
        cancelled.searchField, textView: editor,
        doCommandBy: #selector(NSResponder.cancelOperation(_:))))
    cancelled.dismissWithoutSelection()
    precondition(cancellations == 2)
  }
}
