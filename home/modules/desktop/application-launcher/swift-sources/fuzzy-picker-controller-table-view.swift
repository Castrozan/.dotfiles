import Cocoa

extension FuzzyPickerController {
    func numberOfRows(in tableView: NSTableView) -> Int {
        return filteredItems.count
    }

    func tableView(_ tableView: NSTableView, viewFor tableColumn: NSTableColumn?, row: Int) -> NSView? {
        let identifier = NSUserInterfaceItemIdentifier("ItemCell")
        var cellView = tableView.makeView(withIdentifier: identifier, owner: nil) as? NSTableCellView

        if cellView == nil {
            cellView = NSTableCellView(frame: .zero)
            let textField = NSTextField(labelWithString: "")
            textField.font = NSFont.systemFont(ofSize: 15)
            textField.textColor = .white
            textField.frame = NSRect(x: 16, y: 0, width: 560, height: 28)
            cellView!.addSubview(textField)
            cellView!.textField = textField
            cellView!.identifier = identifier
        }

        cellView!.textField?.stringValue = filteredItems[row]
        return cellView
    }

    func tableView(_ tableView: NSTableView, rowViewForRow row: Int) -> NSTableRowView? {
        return PickerRowView()
    }
}
