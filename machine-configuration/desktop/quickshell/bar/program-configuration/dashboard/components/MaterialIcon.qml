import ".."

StyledText {
    property real fill
    property int grade: -25

    font.family: Appearance.font.family.material
    font.pointSize: Appearance.font.size.larger
    font.variableAxes: ({
        FILL: fill.toFixed(1),
        GRAD: grade,
        opsz: fontInfo.pixelSize,
        wght: fontInfo.weight
    })
}
