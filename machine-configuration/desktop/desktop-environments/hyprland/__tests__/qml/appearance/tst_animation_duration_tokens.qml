import QtQuick
import QtTest

AppearanceFixture {
    id: root

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
}
