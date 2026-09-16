import QtQuick
import QtTest

WorkspacePagesFixture {
    id: root

    TestCase {
        name: "WorkspacesModuleWarningSlot"

        function test_warning_slot_is_index_3() {
            compare(workspacesModule.warningSlotIndex, 3);
        }

        function test_only_warning_slot_returns_true() {
            for (var i = 0; i < 7; i++) {
                if (i === 3)
                    verify(workspacesModule.isSlotWarning(i));
                else
                    verify(!workspacesModule.isSlotWarning(i));
            }
        }
    }
}
