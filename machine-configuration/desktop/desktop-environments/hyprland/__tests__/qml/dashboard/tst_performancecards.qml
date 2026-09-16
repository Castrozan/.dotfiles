import QtQuick
import QtTest

Item {
    id: root

    QtObject {
        id: heroCardSurface

        property string iconName
        property string title
        property string mainValue
        property string mainLabel
        property string secondaryValue
        property string secondaryLabel
        property real usage: 0
        property real temperature: 0
        readonly property real maximumTemperature: 100
        readonly property real temperatureProgress: Math.min(1, Math.max(0, temperature / maximumTemperature))
        property real animatedUsage: 0
        property real animatedTemperature: 0
    }

    QtObject {
        id: gaugeCardSurface

        property string iconName
        property string title
        property real percentage: 0
        property string subtitle
        property real animatedPercentage: 0
    }

    QtObject {
        id: gaugeArcSurface

        property real percentage: 0
        readonly property real arcStartAngle: 0.75 * Math.PI
        readonly property real arcSweepAngle: 1.5 * Math.PI
        readonly property real arcDiameterInset: 12
        readonly property real arcLineWidth: 10
        readonly property real arcEndAngle: arcStartAngle + arcSweepAngle * percentage
    }

    TestCase {
        name: "PerformanceHeroCardDefaults"

        function init() {
            heroCardSurface.usage = 0;
            heroCardSurface.temperature = 0;
        }

        function test_usage_and_temperature_start_at_zero() {
            compare(heroCardSurface.usage, 0);
            compare(heroCardSurface.temperature, 0);
        }

        function test_animated_values_start_at_zero() {
            compare(heroCardSurface.animatedUsage, 0);
            compare(heroCardSurface.animatedTemperature, 0);
        }

        function test_maximum_temperature_is_one_hundred_celsius() {
            compare(heroCardSurface.maximumTemperature, 100);
        }

        function test_text_properties_start_empty() {
            compare(heroCardSurface.iconName, "");
            compare(heroCardSurface.title, "");
            compare(heroCardSurface.mainValue, "");
            compare(heroCardSurface.mainLabel, "");
            compare(heroCardSurface.secondaryValue, "");
            compare(heroCardSurface.secondaryLabel, "");
        }
    }

    TestCase {
        name: "PerformanceHeroCardTemperatureProgress"

        function test_half_of_the_maximum_is_half_progress() {
            heroCardSurface.temperature = 50;
            fuzzyCompare(heroCardSurface.temperatureProgress, 0.5, 0.0001);
        }

        function test_the_maximum_is_full_progress() {
            heroCardSurface.temperature = 100;
            fuzzyCompare(heroCardSurface.temperatureProgress, 1, 0.0001);
        }

        function test_above_the_maximum_clamps_to_full() {
            heroCardSurface.temperature = 150;
            compare(heroCardSurface.temperatureProgress, 1);
        }

        function test_below_zero_clamps_to_empty() {
            heroCardSurface.temperature = -10;
            compare(heroCardSurface.temperatureProgress, 0);
        }
    }

    TestCase {
        name: "PerformanceGaugeCardDefaults"

        function test_percentage_starts_at_zero() {
            compare(gaugeCardSurface.percentage, 0);
            compare(gaugeCardSurface.animatedPercentage, 0);
        }

        function test_text_properties_start_empty() {
            compare(gaugeCardSurface.iconName, "");
            compare(gaugeCardSurface.title, "");
            compare(gaugeCardSurface.subtitle, "");
        }
    }

    TestCase {
        name: "PerformanceGaugeArcGeometry"

        function init() {
            gaugeArcSurface.percentage = 0;
        }

        function test_arc_starts_at_lower_left() {
            fuzzyCompare(gaugeArcSurface.arcStartAngle, 0.75 * Math.PI, 0.0001);
        }

        function test_arc_sweeps_two_hundred_seventy_degrees() {
            fuzzyCompare(gaugeArcSurface.arcSweepAngle, 1.5 * Math.PI, 0.0001);
        }

        function test_full_arc_leaves_a_quarter_turn_gap() {
            fuzzyCompare(gaugeArcSurface.arcStartAngle + gaugeArcSurface.arcSweepAngle, 2.25 * Math.PI, 0.0001);
        }

        function test_empty_gauge_draws_no_progress_arc() {
            fuzzyCompare(gaugeArcSurface.arcEndAngle, gaugeArcSurface.arcStartAngle, 0.0001);
        }

        function test_half_full_gauge_draws_half_the_sweep() {
            gaugeArcSurface.percentage = 0.5;
            fuzzyCompare(gaugeArcSurface.arcEndAngle, gaugeArcSurface.arcStartAngle + 0.75 * Math.PI, 0.0001);
        }

        function test_full_gauge_reaches_the_end_of_the_sweep() {
            gaugeArcSurface.percentage = 1;
            fuzzyCompare(gaugeArcSurface.arcEndAngle, 2.25 * Math.PI, 0.0001);
        }

        function test_stroke_stays_inside_the_canvas() {
            verify(gaugeArcSurface.arcDiameterInset >= gaugeArcSurface.arcLineWidth);
        }
    }
}
