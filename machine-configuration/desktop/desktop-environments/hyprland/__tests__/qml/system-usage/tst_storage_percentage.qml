import QtQuick
import QtTest

SystemUsageFixture {
    id: root

    TestCase {
        name: "SystemUsageServiceStoragePercentage"

        function test_single_disk() {
            systemUsageLogic.disks = [
                {
                    used: 500,
                    total: 1000
                }
            ];
            fuzzyCompare(systemUsageLogic.storagePercentage, 0.5, 0.001);
        }

        function test_multiple_disks() {
            systemUsageLogic.disks = [
                {
                    used: 200,
                    total: 1000
                },
                {
                    used: 300,
                    total: 1000
                }
            ];
            fuzzyCompare(systemUsageLogic.storagePercentage, 0.25, 0.001);
        }

        function test_empty_disks() {
            systemUsageLogic.disks = [];
            compare(systemUsageLogic.storagePercentage, 0);
        }

        function test_zero_total_size() {
            systemUsageLogic.disks = [
                {
                    used: 0,
                    total: 0
                }
            ];
            compare(systemUsageLogic.storagePercentage, 0);
        }

        function test_full_disk() {
            systemUsageLogic.disks = [
                {
                    used: 500,
                    total: 500
                }
            ];
            fuzzyCompare(systemUsageLogic.storagePercentage, 1.0, 0.001);
        }
    }
}
