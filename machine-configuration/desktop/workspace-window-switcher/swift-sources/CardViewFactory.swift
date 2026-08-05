import AppKit

struct WindowCardViews {
    let cardView: NSView
    let borderView: NSView
}

final class WindowCardViewFactory {
    private let iconProvider: IconProviding
    private let cardWidth: CGFloat
    private let cardHeight: CGFloat
    private let cardIconSize: CGFloat
    private let cardCornerRadius: CGFloat
    private let selectionBorderWidth: CGFloat
    private let cardIconTopPadding: CGFloat
    private let cardTitleHorizontalInset: CGFloat
    private let cardTitleBottomOffset: CGFloat
    private let cardTitleHeight: CGFloat

    init(
        iconProvider: IconProviding,
        cardWidth: CGFloat,
        cardHeight: CGFloat,
        cardIconSize: CGFloat,
        cardCornerRadius: CGFloat,
        selectionBorderWidth: CGFloat,
        cardIconTopPadding: CGFloat,
        cardTitleHorizontalInset: CGFloat,
        cardTitleBottomOffset: CGFloat,
        cardTitleHeight: CGFloat
    ) {
        self.iconProvider = iconProvider
        self.cardWidth = cardWidth
        self.cardHeight = cardHeight
        self.cardIconSize = cardIconSize
        self.cardCornerRadius = cardCornerRadius
        self.selectionBorderWidth = selectionBorderWidth
        self.cardIconTopPadding = cardIconTopPadding
        self.cardTitleHorizontalInset = cardTitleHorizontalInset
        self.cardTitleBottomOffset = cardTitleBottomOffset
        self.cardTitleHeight = cardTitleHeight
    }

    func makeCard(
        forWindow window: WorkspaceWindow,
        horizontalOffset: CGFloat,
        verticalOffset: CGFloat
    ) -> WindowCardViews {
        let cardFrame = NSRect(x: horizontalOffset, y: verticalOffset, width: cardWidth, height: cardHeight)
        let cardView = NSView(frame: cardFrame)
        cardView.wantsLayer = true
        cardView.layer?.cornerRadius = cardCornerRadius

        let borderView = makeBorderOverlay()
        cardView.addSubview(borderView)

        let iconImageView = makeIconImageView(forApplicationName: window.applicationName)
        cardView.addSubview(iconImageView)

        let titleTextField = makeTitleTextField(windowTitle: window.title)
        cardView.addSubview(titleTextField)

        return WindowCardViews(cardView: cardView, borderView: borderView)
    }

    private func makeBorderOverlay() -> NSView {
        let borderView = NSView(frame: NSRect(x: 0, y: 0, width: cardWidth, height: cardHeight))
        borderView.wantsLayer = true
        borderView.layer?.cornerRadius = cardCornerRadius
        borderView.layer?.borderWidth = selectionBorderWidth
        return borderView
    }

    private func makeIconImageView(forApplicationName applicationName: String) -> NSImageView {
        let horizontalOffset = (cardWidth - cardIconSize) / 2
        let verticalOffset = cardHeight - cardIconSize - cardIconTopPadding
        let imageView = NSImageView(frame: NSRect(
            x: horizontalOffset,
            y: verticalOffset,
            width: cardIconSize,
            height: cardIconSize
        ))
        imageView.image = iconProvider.iconForApplicationName(applicationName)
        imageView.imageScaling = .scaleProportionallyUpOrDown
        return imageView
    }

    private func makeTitleTextField(windowTitle: String) -> NSTextField {
        let titleFrame = NSRect(
            x: cardTitleHorizontalInset,
            y: cardTitleBottomOffset,
            width: cardWidth - cardTitleHorizontalInset * 2,
            height: cardTitleHeight
        )
        let textField = NSTextField(frame: titleFrame)
        textField.stringValue = windowTitle
        textField.isBezeled = false
        textField.drawsBackground = false
        textField.isEditable = false
        textField.isSelectable = false
        textField.alignment = .center
        textField.lineBreakMode = .byTruncatingTail
        textField.maximumNumberOfLines = 2
        return textField
    }
}

final class CardSelectionStyler {
    private let titleFontSize: CGFloat

    init(titleFontSize: CGFloat) {
        self.titleFontSize = titleFontSize
    }

    func applyStyle(toCardViews cardViews: WindowCardViews, isSelected: Bool) {
        if isSelected {
            cardViews.cardView.layer?.backgroundColor = NSColor.controlAccentColor.withAlphaComponent(0.2).cgColor
            cardViews.borderView.layer?.borderColor = NSColor.controlAccentColor.withAlphaComponent(0.8).cgColor
        } else {
            cardViews.cardView.layer?.backgroundColor = NSColor.white.withAlphaComponent(0.05).cgColor
            cardViews.borderView.layer?.borderColor = NSColor.clear.cgColor
        }
        applyTitleStyle(toCardView: cardViews.cardView, isSelected: isSelected)
    }

    private func applyTitleStyle(toCardView cardView: NSView, isSelected: Bool) {
        let textAlpha: CGFloat = isSelected ? 1.0 : 0.6
        let fontWeight: NSFont.Weight = isSelected ? .medium : .regular
        for subview in cardView.subviews {
            if let textField = subview as? NSTextField {
                textField.textColor = NSColor.white.withAlphaComponent(textAlpha)
                textField.font = NSFont.systemFont(ofSize: titleFontSize, weight: fontWeight)
            }
        }
    }
}
