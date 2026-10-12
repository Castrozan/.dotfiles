import QtQuick

QtObject {
    property int x: 0
    property int y: 0
    property int width: 0
    property int height: 0
    property int intersection: Intersection.Combine
    property list<QtObject> regions: []
}
