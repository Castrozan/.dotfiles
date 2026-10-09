import QtQuick

QtObject {
    id: serviceActivity

    required property QtObject service
    property bool active: false
    property bool initialized: false
    property bool registered: false

    function updateRegistration(): void {
        if (!initialized || registered === active)
            return;
        registered = active;
        service.refCount += active ? 1 : -1;
    }

    onActiveChanged: updateRegistration()

    Component.onCompleted: {
        initialized = true;
        updateRegistration();
    }

    Component.onDestruction: {
        if (registered)
            service.refCount--;
    }
}
