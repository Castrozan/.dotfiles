import QtQuick
import QtTest

SystemUsageFixture {
    id: root

    TestCase {
        name: "SystemUsageServiceFormatKibibytes"

        function test_small_value_returns_kib() {
            var result = systemUsageLogic.formatKibibytes(512);
            compare(result.unit, "KiB");
            compare(result.value, 512);
        }

        function test_zero_returns_kib() {
            var result = systemUsageLogic.formatKibibytes(0);
            compare(result.unit, "KiB");
            compare(result.value, 0);
        }

        function test_exactly_one_mib() {
            var result = systemUsageLogic.formatKibibytes(1024);
            compare(result.unit, "MiB");
            fuzzyCompare(result.value, 1.0, 0.001);
        }

        function test_several_mib() {
            var result = systemUsageLogic.formatKibibytes(2048);
            compare(result.unit, "MiB");
            fuzzyCompare(result.value, 2.0, 0.001);
        }

        function test_exactly_one_gib() {
            var result = systemUsageLogic.formatKibibytes(1024 * 1024);
            compare(result.unit, "GiB");
            fuzzyCompare(result.value, 1.0, 0.001);
        }

        function test_sixteen_gib() {
            var result = systemUsageLogic.formatKibibytes(16 * 1024 * 1024);
            compare(result.unit, "GiB");
            fuzzyCompare(result.value, 16.0, 0.001);
        }

        function test_exactly_one_tib() {
            var result = systemUsageLogic.formatKibibytes(1024 * 1024 * 1024);
            compare(result.unit, "TiB");
            fuzzyCompare(result.value, 1.0, 0.001);
        }

        function test_just_under_one_mib() {
            var result = systemUsageLogic.formatKibibytes(1023);
            compare(result.unit, "KiB");
            compare(result.value, 1023);
        }

        function test_just_under_one_gib() {
            var result = systemUsageLogic.formatKibibytes(1024 * 1024 - 1);
            compare(result.unit, "MiB");
        }
    }
}
