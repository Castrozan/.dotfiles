import QtQuick

MouseArea {
    id: interactionsRoot

    required property real barWidth
    required property var barComponent

    property bool isOverBar: false

    signal popoutAreaLeft

    hoverEnabled: true
    acceptedButtons: Qt.NoButton
    propagateComposedEvents: true

    onBarWidthChanged: {
        if (barWidth === 0)
            isOverBar = false;
    }

    onMouseXChanged: mouse => {
        let wasOverBar = isOverBar;
        isOverBar = mouseX < barWidth;

        if (isOverBar && barComponent) {
            barComponent.checkPopout(mouseY);
        }

        if (wasOverBar && !isOverBar && mouseX > barWidth + 320) {
            popoutAreaLeft();
        }
    }

    onExited: {
        isOverBar = false;
        popoutAreaLeft();
    }

    WheelHandler {
        property: ""
        onWheel: event => {
            if (interactionsRoot.mouseX < interactionsRoot.barWidth && barComponent) {
                barComponent.handleWheel(interactionsRoot.mouseY, event.angleDelta);
            }
        }
    }
}
