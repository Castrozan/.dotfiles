import Cocoa

class PickerRowView: NSTableRowView {
    override func drawSelection(in dirtyRect: NSRect) {
        if selectionHighlightStyle != .none {
            NSColor(white: 0.3, alpha: 1.0).setFill()
            bounds.fill()
        }
    }
}
