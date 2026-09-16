import QtQuick
import QtTest
import "../../../../quickshell/bar/program-configuration/dashboard/services/system-usage"

Item {
    property var disks: []
    StorageUsage {
        id: storage
        onDisksRead: discovered => disks = discovered
    }
    TestCase {
        name: "StorageUsage"
        function test_partition_sizes_and_usage_are_aggregated() {
            storage.stdout.read('NAME="sda" SIZE="4096" TYPE="disk"\nNAME="sda1" SIZE="2048" TYPE="part" FSUSED="512" FSSIZE="1024"\nNAME="sda2" SIZE="2048" TYPE="part" FSUSED="256" FSSIZE="1024"\n');
            compare(disks, [
                {
                    mount: "sda",
                    used: 0.75,
                    total: 2,
                    free: 1.25,
                    perc: 0.375
                }
            ]);
        }
        function test_nvme_parent_disk_is_preserved() {
            storage.stdout.read('NAME="nvme0n1" SIZE="8192" TYPE="disk"\nNAME="nvme0n1p1" TYPE="part" FSUSED="1024" FSSIZE="4096"\n');
            compare(disks, [
                {
                    mount: "nvme0n1",
                    used: 1,
                    total: 4,
                    free: 3,
                    perc: 0.25
                }
            ]);
        }
        function test_zram_and_invalid_records_are_skipped() {
            storage.stdout.read('invalid\nNAME="zram0" SIZE="8192" TYPE="disk"\n');
            compare(disks, []);
        }
        function test_disk_size_is_used_without_filesystems() {
            storage.stdout.read('NAME="sdb" SIZE="4096" TYPE="disk"\n');
            compare(disks, [
                {
                    mount: "sdb",
                    used: 0,
                    total: 4,
                    free: 4,
                    perc: 0
                }
            ]);
        }
    }
}
