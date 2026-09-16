import QtQuick

QtObject {
    property url path
    property bool watchChanges: false
    property bool blockLoading: false
    property bool loaded: true
    property string mockText: "{}"

    signal fileChanged()

    function text(): string {
        return mockText;
    }

    function reload(): void {}
}
