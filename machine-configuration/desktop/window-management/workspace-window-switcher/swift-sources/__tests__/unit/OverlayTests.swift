import AppKit

private final class TestApplicationIcons: IconProviding {
  let icon = NSImage(size: NSSize(width: 64, height: 64))
  func prewarmCacheFromRunningApplications() {}
  func iconForApplicationName(_ applicationName: String) -> NSImage { icon }
}

enum OverlayTests {
  static func runAll() {
    let icons = TestApplicationIcons()
    let factory = WindowCardViewFactory(
      iconProvider: icons, cardWidth: 140, cardHeight: 120,
      cardIconSize: 64, cardCornerRadius: 10, selectionBorderWidth: 3,
      cardIconTopPadding: 16, cardTitleHorizontalInset: 6, cardTitleBottomOffset: 4,
      cardTitleHeight: 28)
    let window = WorkspaceWindow(identifier: 1, applicationName: "Terminal", title: "Build output")
    let card = factory.makeCard(forWindow: window, horizontalOffset: 16, verticalOffset: 16)
    precondition(card.cardView.frame == NSRect(x: 16, y: 16, width: 140, height: 120))
    precondition(card.borderView.layer?.borderWidth == 3)
    let image = card.cardView.subviews.compactMap { $0 as? NSImageView }.first!
    precondition(image.image === icons.icon && image.frame.size == NSSize(width: 64, height: 64))
    let title = card.cardView.subviews.compactMap { $0 as? NSTextField }.first!
    precondition(title.stringValue == "Build output" && !title.isEditable)
    let styler = CardSelectionStyler(titleFontSize: 11)
    styler.applyStyle(toCardViews: card, isSelected: true)
    precondition(title.textColor?.alphaComponent == 1)
    styler.applyStyle(toCardViews: card, isSelected: false)
    precondition(abs(title.textColor!.alphaComponent - 0.6) < 0.001)
    let empty = OverlayLayoutCalculator.calculateOverlayDimensions(
      cardCount: 0, cardWidth: 140,
      cardHeight: 120, cardSpacing: 12, overlayPadding: 16)
    precondition(empty.totalWidth == 32 && empty.totalHeight == 152)
    let panel = SwitcherOverlayPanel(
      cardViewFactory: factory, selectionStyler: styler,
      cardWidth: 140, cardHeight: 120, cardSpacing: 12, overlayPadding: 16, overlayCornerRadius: 14)
    panel.hide()
    panel.showWithWindowsAndSelection([window, window], selectedIndex: 0)
    let visible = NSApp.windows.compactMap { $0 as? NonActivatingFloatingPanel }.first {
      $0.isVisible
    }!
    precondition(!visible.canBecomeKey && !visible.canBecomeMain && visible.ignoresMouseEvents)
    precondition(visible.frame.size == NSSize(width: 324, height: 152))
    let cards = visible.contentView!.subviews.first!.subviews
    precondition(cards.count == 2 && cards[1].frame.origin.x == 168)
    panel.updateSelectedIndex(1)
    let selectedTitle = cards[1].subviews.compactMap { $0 as? NSTextField }.first!
    precondition(selectedTitle.textColor?.alphaComponent == 1)
    panel.hide()
    precondition(!visible.isVisible)
  }
}
