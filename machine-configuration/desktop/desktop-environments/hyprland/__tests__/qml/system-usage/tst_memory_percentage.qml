import QtQuick
import QtTest

SystemUsageFixture {
    id: root

    TestCase {
        name: "SystemUsageServiceMemoryPercentage"

        function test_normal_memory_usage() {
            systemUsageLogic.memoryTotalKib = 16 * 1024 * 1024;
            systemUsageLogic.memoryUsedKib = 8 * 1024 * 1024;
            fuzzyCompare(systemUsageLogic.memoryPercentage, 0.5, 0.001);
        }

        function test_zero_total_returns_zero() {
            systemUsageLogic.memoryTotalKib = 0;
            systemUsageLogic.memoryUsedKib = 1000;
            compare(systemUsageLogic.memoryPercentage, 0);
        }

        function test_full_memory() {
            systemUsageLogic.memoryTotalKib = 1000;
            systemUsageLogic.memoryUsedKib = 1000;
            fuzzyCompare(systemUsageLogic.memoryPercentage, 1.0, 0.001);
        }

        function test_no_memory_used() {
            systemUsageLogic.memoryTotalKib = 1000;
            systemUsageLogic.memoryUsedKib = 0;
            compare(systemUsageLogic.memoryPercentage, 0);
        }
    }
}
