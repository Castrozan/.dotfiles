import QtQuick
import QtTest

AppearanceFixture {
    id: root

    TestCase {
        name: "AppearanceAnimationCurveTokens"

        function test_all_curves_have_six_control_points() {
            compare(appearance.anim.curves.standard.length, 6);
            compare(appearance.anim.curves.standardAccel.length, 6);
            compare(appearance.anim.curves.standardDecel.length, 6);
            compare(appearance.anim.curves.emphasized.length, 6);
            compare(appearance.anim.curves.expressiveDefaultSpatial.length, 6);
            compare(appearance.anim.curves.expressiveFastSpatial.length, 6);
        }

        function test_all_curves_end_at_1_1() {
            var curveNames = ["standard", "standardAccel", "standardDecel", "emphasized", "expressiveDefaultSpatial", "expressiveFastSpatial"];
            for (var i = 0; i < curveNames.length; i++) {
                var curve = appearance.anim.curves[curveNames[i]];
                fuzzyCompare(curve[4], 1.0, 0.001, curveNames[i] + " end x should be 1.0");
                fuzzyCompare(curve[5], 1.0, 0.001, curveNames[i] + " end y should be 1.0");
            }
        }

        function test_curve_values_are_in_valid_range() {
            var curveNames = ["standard", "standardAccel", "standardDecel", "emphasized", "expressiveDefaultSpatial", "expressiveFastSpatial"];
            for (var i = 0; i < curveNames.length; i++) {
                var curve = appearance.anim.curves[curveNames[i]];
                for (var j = 0; j < curve.length; j++) {
                    verify(curve[j] >= 0.0 && curve[j] <= 1.0, curveNames[i] + " point " + j + " value " + curve[j] + " out of [0,1] range");
                }
            }
        }
    }
}
