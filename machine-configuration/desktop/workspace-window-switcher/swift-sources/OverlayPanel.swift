import AppKit

final class NonActivatingFloatingPanel: NSPanel {
    override var canBecomeKey: Bool { false }
    override var canBecomeMain: Bool { false }
}

enum NonActivatingFloatingPanelFactory {
    static func makeFloatingPanel() -> NonActivatingFloatingPanel {
        let initialContentFrame = NSRect(x: 0, y: 0, width: 400, height: 200)
        let styleMask: NSWindow.StyleMask = [.borderless, .nonactivatingPanel]
        let panel = NonActivatingFloatingPanel(
            contentRect: initialContentFrame,
            styleMask: styleMask,
            backing: .buffered,
            defer: false
        )
        panel.isReleasedWhenClosed = false
        panel.level = .popUpMenu
        panel.isOpaque = false
        panel.backgroundColor = .clear
        panel.hasShadow = true
        panel.ignoresMouseEvents = true
        panel.hidesOnDeactivate = false
        panel.alphaValue = 1.0
        panel.collectionBehavior = [.canJoinAllSpaces, .stationary]
        return panel
    }
}

struct OverlayLayoutDimensions {
    let totalWidth: CGFloat
    let totalHeight: CGFloat
}

enum OverlayLayoutCalculator {
    static func calculateOverlayDimensions(
        cardCount: Int,
        cardWidth: CGFloat,
        cardHeight: CGFloat,
        cardSpacing: CGFloat,
        overlayPadding: CGFloat
    ) -> OverlayLayoutDimensions {
        let cardCountFloat = CGFloat(cardCount)
        let totalWidth = overlayPadding * 2
            + cardCountFloat * cardWidth
            + max(0, cardCountFloat - 1) * cardSpacing
        let totalHeight = overlayPadding * 2 + cardHeight
        return OverlayLayoutDimensions(totalWidth: totalWidth, totalHeight: totalHeight)
    }

    static func horizontalOffsetForCard(
        atIndex index: Int,
        cardWidth: CGFloat,
        cardSpacing: CGFloat,
        overlayPadding: CGFloat
    ) -> CGFloat {
        return overlayPadding + CGFloat(index) * (cardWidth + cardSpacing)
    }
}

enum BackgroundContainerViewFactory {
    static func makeBackgroundContainerView(
        width: CGFloat,
        height: CGFloat,
        cornerRadius: CGFloat
    ) -> NSView {
        let frame = NSRect(x: 0, y: 0, width: width, height: height)
        let visualEffectView = NSVisualEffectView(frame: frame)
        visualEffectView.material = .hudWindow
        visualEffectView.blendingMode = .behindWindow
        visualEffectView.state = .active
        visualEffectView.wantsLayer = true
        visualEffectView.layer?.cornerRadius = cornerRadius
        visualEffectView.layer?.masksToBounds = true
        visualEffectView.layer?.backgroundColor = NSColor.black.withAlphaComponent(0.7).cgColor
        return visualEffectView
    }
}

final class SwitcherOverlayPanel: OverlayRendering {
    private let cardViewFactory: WindowCardViewFactory
    private let selectionStyler: CardSelectionStyler
    private let cardWidth: CGFloat
    private let cardHeight: CGFloat
    private let cardSpacing: CGFloat
    private let overlayPadding: CGFloat
    private let overlayCornerRadius: CGFloat

    private var floatingPanel: NonActivatingFloatingPanel?
    private var backgroundContainerView: NSView?
    private var cardViewsByDisplayIndex: [WindowCardViews] = []

    init(
        cardViewFactory: WindowCardViewFactory,
        selectionStyler: CardSelectionStyler,
        cardWidth: CGFloat,
        cardHeight: CGFloat,
        cardSpacing: CGFloat,
        overlayPadding: CGFloat,
        overlayCornerRadius: CGFloat
    ) {
        self.cardViewFactory = cardViewFactory
        self.selectionStyler = selectionStyler
        self.cardWidth = cardWidth
        self.cardHeight = cardHeight
        self.cardSpacing = cardSpacing
        self.overlayPadding = overlayPadding
        self.overlayCornerRadius = overlayCornerRadius
    }

    func showWithWindowsAndSelection(_ windows: [WorkspaceWindow], selectedIndex: Int) {
        let panel = NonActivatingFloatingPanelFactory.makeFloatingPanel()
        floatingPanel = panel
        buildOverlayContents(windows: windows, selectedIndex: selectedIndex, panel: panel)
        centerPanelOnMainScreen(panel)
        panel.orderFrontRegardless()
    }

    func updateSelectedIndex(_ selectedIndex: Int) {
        for (cardIndex, cardViews) in cardViewsByDisplayIndex.enumerated() {
            selectionStyler.applyStyle(toCardViews: cardViews, isSelected: cardIndex == selectedIndex)
        }
    }

    func hide() {
        if let panel = floatingPanel {
            panel.orderOut(nil)
            panel.close()
        }
        floatingPanel = nil
        backgroundContainerView = nil
        cardViewsByDisplayIndex = []
    }

    private func buildOverlayContents(
        windows: [WorkspaceWindow],
        selectedIndex: Int,
        panel: NonActivatingFloatingPanel
    ) {
        let dimensions = OverlayLayoutCalculator.calculateOverlayDimensions(
            cardCount: windows.count,
            cardWidth: cardWidth,
            cardHeight: cardHeight,
            cardSpacing: cardSpacing,
            overlayPadding: overlayPadding
        )
        panel.setFrame(
            NSRect(x: 0, y: 0, width: dimensions.totalWidth, height: dimensions.totalHeight),
            display: false
        )

        let backgroundView = BackgroundContainerViewFactory.makeBackgroundContainerView(
            width: dimensions.totalWidth,
            height: dimensions.totalHeight,
            cornerRadius: overlayCornerRadius
        )
        panel.contentView?.addSubview(backgroundView)
        backgroundContainerView = backgroundView

        for (windowIndex, window) in windows.enumerated() {
            let horizontalOffset = OverlayLayoutCalculator.horizontalOffsetForCard(
                atIndex: windowIndex,
                cardWidth: cardWidth,
                cardSpacing: cardSpacing,
                overlayPadding: overlayPadding
            )
            let cardViews = cardViewFactory.makeCard(
                forWindow: window,
                horizontalOffset: horizontalOffset,
                verticalOffset: overlayPadding
            )
            selectionStyler.applyStyle(toCardViews: cardViews, isSelected: windowIndex == selectedIndex)
            backgroundView.addSubview(cardViews.cardView)
            cardViewsByDisplayIndex.append(cardViews)
        }
    }

    private func centerPanelOnMainScreen(_ panel: NonActivatingFloatingPanel) {
        guard let screen = NSScreen.main else { return }
        let screenFrame = screen.frame
        let panelFrame = panel.frame
        let centeredX = (screenFrame.size.width - panelFrame.size.width) / 2
        let centeredY = (screenFrame.size.height - panelFrame.size.height) / 2
        panel.setFrameOrigin(NSPoint(x: centeredX, y: centeredY))
    }
}
