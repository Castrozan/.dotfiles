import QtQuick
import QtTest

Item {
    id: root

    QtObject {
        id: appearance

        readonly property var spacing: QtObject {
            readonly property int smaller: 4
            readonly property int small: 8
            readonly property int normal: 12
            readonly property int large: 16
        }

        readonly property var padding: QtObject {
            readonly property int smaller: 4
            readonly property int small: 8
            readonly property int normal: 12
            readonly property int large: 16
        }

        readonly property var rounding: QtObject {
            readonly property int small: 8
            readonly property int normal: 12
            readonly property int large: 16
            readonly property int full: 999
            readonly property real scale: 1.0
        }

        readonly property var font: QtObject {
            readonly property var family: QtObject {
                readonly property string sans: "JetBrainsMono Nerd Font"
                readonly property string material: "Material Symbols Rounded"
                readonly property string clock: "JetBrainsMono Nerd Font"
            }

            readonly property var size: QtObject {
                readonly property int smaller: 9
                readonly property int small: 10
                readonly property int normal: 12
                readonly property int large: 14
                readonly property int larger: 16
                readonly property int extraLarge: 20
            }
        }

        readonly property var anim: QtObject {
            readonly property var durations: QtObject {
                readonly property int small: 150
                readonly property int normal: 250
                readonly property int large: 400
                readonly property int extraLarge: 1000
                readonly property int expressiveDefaultSpatial: 500
                readonly property int expressiveFastSpatial: 200
            }

            readonly property var curves: QtObject {
                readonly property var standard: [0.2, 0.0, 0, 1.0, 1, 1]
                readonly property var standardAccel: [0.3, 0, 0.8, 0.15, 1, 1]
                readonly property var standardDecel: [0.05, 0.7, 0.1, 1.0, 1, 1]
                readonly property var emphasized: [0.2, 0, 0, 1.0, 1, 1]
                readonly property var expressiveDefaultSpatial: [0.34, 0, 0, 1, 1, 1]
                readonly property var expressiveFastSpatial: [0.1, 0, 0, 1, 1, 1]
            }
        }
    }

    TestCase {
        name: "AppearanceSpacingTokens"

        function test_all_spacing_values_are_positive() {
            verify(appearance.spacing.smaller > 0);
            verify(appearance.spacing.small > 0);
            verify(appearance.spacing.normal > 0);
            verify(appearance.spacing.large > 0);
        }

        function test_spacing_increases_monotonically() {
            verify(appearance.spacing.smaller <= appearance.spacing.small);
            verify(appearance.spacing.small <= appearance.spacing.normal);
            verify(appearance.spacing.normal <= appearance.spacing.large);
        }

        function test_spacing_exact_values() {
            compare(appearance.spacing.smaller, 4);
            compare(appearance.spacing.small, 8);
            compare(appearance.spacing.normal, 12);
            compare(appearance.spacing.large, 16);
        }
    }

    TestCase {
        name: "AppearancePaddingTokens"

        function test_all_padding_values_are_positive() {
            verify(appearance.padding.smaller > 0);
            verify(appearance.padding.small > 0);
            verify(appearance.padding.normal > 0);
            verify(appearance.padding.large > 0);
        }

        function test_padding_increases_monotonically() {
            verify(appearance.padding.smaller <= appearance.padding.small);
            verify(appearance.padding.small <= appearance.padding.normal);
            verify(appearance.padding.normal <= appearance.padding.large);
        }

        function test_padding_exact_values() {
            compare(appearance.padding.smaller, 4);
            compare(appearance.padding.small, 8);
            compare(appearance.padding.normal, 12);
            compare(appearance.padding.large, 16);
        }
    }

    TestCase {
        name: "AppearanceRoundingTokens"

        function test_all_rounding_values_are_positive() {
            verify(appearance.rounding.small > 0);
            verify(appearance.rounding.normal > 0);
            verify(appearance.rounding.large > 0);
            verify(appearance.rounding.full > 0);
        }

        function test_rounding_increases_monotonically() {
            verify(appearance.rounding.small <= appearance.rounding.normal);
            verify(appearance.rounding.normal <= appearance.rounding.large);
            verify(appearance.rounding.large <= appearance.rounding.full);
        }

        function test_full_rounding_is_large_value() {
            verify(appearance.rounding.full >= 100);
        }

        function test_scale_is_positive() {
            verify(appearance.rounding.scale > 0);
        }

        function test_rounding_exact_values() {
            compare(appearance.rounding.small, 8);
            compare(appearance.rounding.normal, 12);
            compare(appearance.rounding.large, 16);
            compare(appearance.rounding.full, 999);
            fuzzyCompare(appearance.rounding.scale, 1.0, 0.001);
        }
    }

    TestCase {
        name: "AppearanceFontFamilyTokens"

        function test_sans_family_is_nonempty() {
            verify(appearance.font.family.sans.length > 0);
        }

        function test_material_family_is_nonempty() {
            verify(appearance.font.family.material.length > 0);
        }

        function test_clock_family_is_nonempty() {
            verify(appearance.font.family.clock.length > 0);
        }

        function test_sans_family_exact_value() {
            compare(appearance.font.family.sans, "JetBrainsMono Nerd Font");
        }

        function test_material_family_exact_value() {
            compare(appearance.font.family.material, "Material Symbols Rounded");
        }
    }

    TestCase {
        name: "AppearanceFontSizeTokens"

        function test_all_sizes_are_positive() {
            verify(appearance.font.size.smaller > 0);
            verify(appearance.font.size.small > 0);
            verify(appearance.font.size.normal > 0);
            verify(appearance.font.size.large > 0);
            verify(appearance.font.size.larger > 0);
            verify(appearance.font.size.extraLarge > 0);
        }

        function test_sizes_increase_monotonically() {
            verify(appearance.font.size.smaller <= appearance.font.size.small);
            verify(appearance.font.size.small <= appearance.font.size.normal);
            verify(appearance.font.size.normal <= appearance.font.size.large);
            verify(appearance.font.size.large <= appearance.font.size.larger);
            verify(appearance.font.size.larger <= appearance.font.size.extraLarge);
        }

        function test_sizes_are_reasonable_pt_values() {
            verify(appearance.font.size.smaller >= 6);
            verify(appearance.font.size.extraLarge <= 72);
        }

        function test_exact_size_values() {
            compare(appearance.font.size.smaller, 9);
            compare(appearance.font.size.small, 10);
            compare(appearance.font.size.normal, 12);
            compare(appearance.font.size.large, 14);
            compare(appearance.font.size.larger, 16);
            compare(appearance.font.size.extraLarge, 20);
        }
    }

    TestCase {
        name: "AppearanceAnimationDurationTokens"

        function test_all_durations_are_positive() {
            verify(appearance.anim.durations.small > 0);
            verify(appearance.anim.durations.normal > 0);
            verify(appearance.anim.durations.large > 0);
            verify(appearance.anim.durations.extraLarge > 0);
            verify(appearance.anim.durations.expressiveDefaultSpatial > 0);
            verify(appearance.anim.durations.expressiveFastSpatial > 0);
        }

        function test_all_durations_under_5000ms() {
            verify(appearance.anim.durations.small < 5000);
            verify(appearance.anim.durations.normal < 5000);
            verify(appearance.anim.durations.large < 5000);
            verify(appearance.anim.durations.extraLarge < 5000);
            verify(appearance.anim.durations.expressiveDefaultSpatial < 5000);
            verify(appearance.anim.durations.expressiveFastSpatial < 5000);
        }

        function test_durations_increase_in_named_order() {
            verify(appearance.anim.durations.small <= appearance.anim.durations.normal);
            verify(appearance.anim.durations.normal <= appearance.anim.durations.large);
            verify(appearance.anim.durations.large <= appearance.anim.durations.extraLarge);
        }

        function test_fast_spatial_is_faster_than_default_spatial() {
            verify(appearance.anim.durations.expressiveFastSpatial < appearance.anim.durations.expressiveDefaultSpatial);
        }

        function test_exact_duration_values() {
            compare(appearance.anim.durations.small, 150);
            compare(appearance.anim.durations.normal, 250);
            compare(appearance.anim.durations.large, 400);
            compare(appearance.anim.durations.extraLarge, 1000);
            compare(appearance.anim.durations.expressiveDefaultSpatial, 500);
            compare(appearance.anim.durations.expressiveFastSpatial, 200);
        }
    }

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
                    verify(curve[j] >= 0.0 && curve[j] <= 1.0,
                        curveNames[i] + " point " + j + " value " + curve[j] + " out of [0,1] range");
                }
            }
        }
    }
}
