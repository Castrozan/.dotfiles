import QtQuick
import QtTest
import "../../../quickshell/overview/program-configuration/modules/overview"

Item {
    id: root

    TestCase {
        name: "OverviewWorkspaceMathSpecialWorkspaceIndex"

        function test_index_locates_a_visible_special_workspace() {
            compare(OverviewWorkspaceMath.specialWorkspaceIndex("music", ["stash", "music"]), 1);
        }

        function test_index_reports_minus_one_when_absent() {
            compare(OverviewWorkspaceMath.specialWorkspaceIndex("music", ["stash"]), -1);
            compare(OverviewWorkspaceMath.specialWorkspaceIndex("stash", undefined), -1);
        }
    }

    TestCase {
        name: "OverviewWorkspaceMathSpecialWorkspaceLabel"

        function test_label_falls_back_for_an_empty_name() {
            compare(OverviewWorkspaceMath.specialWorkspaceLabel(""), "Special");
            compare(OverviewWorkspaceMath.specialWorkspaceLabel("   "), "Special");
            compare(OverviewWorkspaceMath.specialWorkspaceLabel(undefined), "Special");
        }

        function test_label_reads_separators_as_spaces() {
            compare(OverviewWorkspaceMath.specialWorkspaceLabel("music-player"), "music player");
            compare(OverviewWorkspaceMath.specialWorkspaceLabel("side_stash"), "side stash");
            compare(OverviewWorkspaceMath.specialWorkspaceLabel("  scratch__pad  "), "scratch pad");
        }
    }

    TestCase {
        name: "OverviewWorkspaceMathNextSpecialWorkspaceName"

        function test_next_name_is_the_base_when_nothing_is_taken() {
            compare(OverviewWorkspaceMath.nextSpecialWorkspaceName([]), "stash");
            compare(OverviewWorkspaceMath.nextSpecialWorkspaceName(undefined), "stash");
            compare(OverviewWorkspaceMath.nextSpecialWorkspaceName(["music"]), "stash");
        }

        function test_next_name_counts_up_past_taken_names() {
            compare(OverviewWorkspaceMath.nextSpecialWorkspaceName(["stash"]), "stash-2");
            compare(OverviewWorkspaceMath.nextSpecialWorkspaceName(["stash", "stash-2"]), "stash-3");
            compare(OverviewWorkspaceMath.nextSpecialWorkspaceName(["stash", "stash-3"]), "stash-2");
        }

        function test_next_name_ignores_case_and_padding() {
            compare(OverviewWorkspaceMath.nextSpecialWorkspaceName([" STASH "]), "stash-2");
            compare(OverviewWorkspaceMath.nextSpecialWorkspaceName(["Stash", "Stash-2"]), "stash-3");
        }
    }
}
