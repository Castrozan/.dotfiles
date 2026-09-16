import QtQuick
import QtTest

SystemUsageFixture {
    id: root

    TestCase {
        name: "SystemUsageServiceCleanCpuName"

        function test_removes_registered_trademark() {
            compare(systemUsageLogic.cleanCpuName("Intel(R) Xeon(R)"), "Intel Xeon");
        }

        function test_removes_trademark() {
            compare(systemUsageLogic.cleanCpuName("Intel(TM) i7"), "Intel i7");
        }

        function test_removes_cpu_keyword() {
            compare(systemUsageLogic.cleanCpuName("Intel Core i7-14700K CPU @ 3.40GHz"), "Intel i7-14700K @ 3.40GHz");
        }

        function test_removes_generation_prefix() {
            compare(systemUsageLogic.cleanCpuName("14th Gen Intel Core i7-14700K"), "Intel i7-14700K");
        }

        function test_removes_2nd_gen() {
            compare(systemUsageLogic.cleanCpuName("2nd Gen Intel Core i5-2500"), "Intel i5-2500");
        }

        function test_removes_3rd_gen() {
            compare(systemUsageLogic.cleanCpuName("3rd Gen Intel Core i7-3770"), "Intel i7-3770");
        }

        function test_removes_1st_gen() {
            compare(systemUsageLogic.cleanCpuName("1st Gen AMD Ryzen"), "AMD Ryzen");
        }

        function test_removes_processor_keyword() {
            compare(systemUsageLogic.cleanCpuName("AMD Ryzen 9 5950X Processor"), "AMD Ryzen 9 5950X");
        }

        function test_removes_core_keyword() {
            compare(systemUsageLogic.cleanCpuName("Intel Core i9-13900K"), "Intel i9-13900K");
        }

        function test_collapses_multiple_spaces() {
            compare(systemUsageLogic.cleanCpuName("Intel    i7   14700K"), "Intel i7 14700K");
        }

        function test_trims_whitespace() {
            compare(systemUsageLogic.cleanCpuName("  Intel i7  "), "Intel i7");
        }

        function test_full_realistic_cpu_name() {
            compare(systemUsageLogic.cleanCpuName("14th Gen Intel(R) Core(TM) i7-14700K CPU @ 3.40GHz"), "Intel i7-14700K @ 3.40GHz");
        }

        function test_amd_cpu_name() {
            compare(systemUsageLogic.cleanCpuName("AMD Ryzen 9 7950X 16-Core Processor"), "AMD Ryzen 9 7950X 16-");
        }

        function test_empty_string() {
            compare(systemUsageLogic.cleanCpuName(""), "");
        }
    }
}
