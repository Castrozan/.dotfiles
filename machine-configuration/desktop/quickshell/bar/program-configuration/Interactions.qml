import QtQuick

MouseArea {
    id: interactionsRoot

    required property int barWidth
    required property var barComponent

    property bool isOverBar: false

    signal popoutAreaLeft()

    hoverEnabled: true
    acceptedButtons: Qt.NoButton
    propagateComposedEvents: true

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
