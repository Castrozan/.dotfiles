import QtQuick

Item {
    id: drawerHoverTimingRoot

    required property bool contentHovered

    property int revealDelayInterval: 200
    property int concealDelayInterval: 450
    property bool triggerHovered: false

    signal revealRequested()
    signal concealRequested()
    signal contentPointerEntered()
    signal contentPointerLeft()

    function triggerEntered(): void {
        drawerHoverTimingRoot.triggerHovered = true;
        concealTimer.stop();
        if (drawerHoverTimingRoot.revealDelayInterval > 0) {
            revealDelayTimer.restart();
            return;
        }
        drawerHoverTimingRoot.revealRequested();
    }

    function triggerLeft(): void {
        drawerHoverTimingRoot.triggerHovered = false;
        revealDelayTimer.stop();
        if (!drawerHoverTimingRoot.contentHovered)
            concealTimer.restart();
    }

    function contentEntered(): void {
        drawerHoverTimingRoot.contentPointerEntered();
        concealTimer.stop();
    }

    function contentLeft(): void {
        drawerHoverTimingRoot.contentPointerLeft();
        if (!drawerHoverTimingRoot.triggerHovered)
            concealTimer.restart();
    }

    Timer {
        id: revealDelayTimer

        interval: drawerHoverTimingRoot.revealDelayInterval
        onTriggered: {
            if (drawerHoverTimingRoot.triggerHovered)
                drawerHoverTimingRoot.revealRequested();
        }
    }

    Timer {
        id: concealTimer

        interval: drawerHoverTimingRoot.concealDelayInterval
        onTriggered: {
            if (!drawerHoverTimingRoot.contentHovered && !drawerHoverTimingRoot.triggerHovered)
                drawerHoverTimingRoot.concealRequested();
        }
    }
}
