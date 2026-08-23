import QtQuick
import QtTest
import "../../../quickshell/overview/program-configuration/modules/overview"

Item {
    id: root

    readonly property var topDownLayout: ({
        rows: 2,
        columns: 5,
        orderBottomUp: false,
        orderRightLeft: false,
        workspaceOffset: 0,
        workspaceGroup: 0
    })

    readonly property var bottomUpLayout: ({
        rows: 2,
        columns: 5,
        orderBottomUp: true,
        orderRightLeft: false,
        workspaceOffset: 0,
        workspaceGroup: 0
    })

    readonly property var rightLeftLayout: ({
        rows: 2,
        columns: 5,
        orderBottomUp: false,
        orderRightLeft: true,
        workspaceOffset: 0,
        workspaceGroup: 0
    })

    readonly property var offsetLayout: ({
        rows: 2,
        columns: 5,
        orderBottomUp: false,
        orderRightLeft: false,
        workspaceOffset: 20,
        workspaceGroup: 0
    })

    readonly property var secondGroupLayout: ({
        rows: 2,
        columns: 5,
        orderBottomUp: false,
        orderRightLeft: false,
        workspaceOffset: 0,
        workspaceGroup: 1
    })

    TestCase {
        name: "OverviewWorkspaceMathRow"

        function test_first_row_holds_the_first_column_run() {
            compare(OverviewWorkspaceMath.workspaceRow(1, root.topDownLayout), 0);
            compare(OverviewWorkspaceMath.workspaceRow(5, root.topDownLayout), 0);
        }

        function test_second_row_starts_after_one_full_row() {
            compare(OverviewWorkspaceMath.workspaceRow(6, root.topDownLayout), 1);
            compare(OverviewWorkspaceMath.workspaceRow(10, root.topDownLayout), 1);
        }

        function test_rows_wrap_within_the_next_group() {
            compare(OverviewWorkspaceMath.workspaceRow(11, root.topDownLayout), 0);
            compare(OverviewWorkspaceMath.workspaceRow(16, root.topDownLayout), 1);
        }

        function test_bottom_up_order_flips_the_row() {
            compare(OverviewWorkspaceMath.workspaceRow(1, root.bottomUpLayout), 1);
            compare(OverviewWorkspaceMath.workspaceRow(6, root.bottomUpLayout), 0);
        }

        function test_offset_shifts_the_row_boundaries() {
            compare(OverviewWorkspaceMath.workspaceRow(21, root.offsetLayout), 0);
            compare(OverviewWorkspaceMath.workspaceRow(26, root.offsetLayout), 1);
        }

        function test_non_finite_workspace_falls_back_to_the_first_row() {
            compare(OverviewWorkspaceMath.workspaceRow(undefined, root.topDownLayout), 0);
            compare(OverviewWorkspaceMath.workspaceRow(NaN, root.topDownLayout), 0);
        }
    }

    TestCase {
        name: "OverviewWorkspaceMathColumn"

        function test_columns_run_left_to_right() {
            compare(OverviewWorkspaceMath.workspaceColumn(1, root.topDownLayout), 0);
            compare(OverviewWorkspaceMath.workspaceColumn(3, root.topDownLayout), 2);
            compare(OverviewWorkspaceMath.workspaceColumn(5, root.topDownLayout), 4);
        }

        function test_second_row_restarts_the_columns() {
            compare(OverviewWorkspaceMath.workspaceColumn(6, root.topDownLayout), 0);
            compare(OverviewWorkspaceMath.workspaceColumn(10, root.topDownLayout), 4);
        }

        function test_right_left_order_mirrors_the_column() {
            compare(OverviewWorkspaceMath.workspaceColumn(1, root.rightLeftLayout), 4);
            compare(OverviewWorkspaceMath.workspaceColumn(5, root.rightLeftLayout), 0);
        }

        function test_offset_shifts_the_column_boundaries() {
            compare(OverviewWorkspaceMath.workspaceColumn(21, root.offsetLayout), 0);
            compare(OverviewWorkspaceMath.workspaceColumn(25, root.offsetLayout), 4);
        }

        function test_non_finite_workspace_falls_back_to_the_first_column() {
            compare(OverviewWorkspaceMath.workspaceColumn(undefined, root.topDownLayout), 0);
            compare(OverviewWorkspaceMath.workspaceColumn(NaN, root.topDownLayout), 0);
        }
    }

    TestCase {
        name: "OverviewWorkspaceMathCell"

        function test_first_cell_is_the_first_workspace() {
            compare(OverviewWorkspaceMath.workspaceInCell(0, 0, root.topDownLayout), 1);
        }

        function test_cells_walk_the_row_then_wrap() {
            compare(OverviewWorkspaceMath.workspaceInCell(0, 4, root.topDownLayout), 5);
            compare(OverviewWorkspaceMath.workspaceInCell(1, 0, root.topDownLayout), 6);
            compare(OverviewWorkspaceMath.workspaceInCell(1, 4, root.topDownLayout), 10);
        }

        function test_second_group_starts_after_every_shown_workspace() {
            compare(OverviewWorkspaceMath.workspaceInCell(0, 0, root.secondGroupLayout), 11);
            compare(OverviewWorkspaceMath.workspaceInCell(1, 4, root.secondGroupLayout), 20);
        }

        function test_offset_shifts_every_cell() {
            compare(OverviewWorkspaceMath.workspaceInCell(0, 0, root.offsetLayout), 21);
            compare(OverviewWorkspaceMath.workspaceInCell(1, 4, root.offsetLayout), 30);
        }

        function test_bottom_up_order_flips_the_cell() {
            compare(OverviewWorkspaceMath.workspaceInCell(0, 0, root.bottomUpLayout), 6);
            compare(OverviewWorkspaceMath.workspaceInCell(1, 0, root.bottomUpLayout), 1);
        }

        function test_right_left_order_mirrors_the_cell() {
            compare(OverviewWorkspaceMath.workspaceInCell(0, 0, root.rightLeftLayout), 5);
            compare(OverviewWorkspaceMath.workspaceInCell(0, 4, root.rightLeftLayout), 1);
        }

        function test_cell_round_trips_through_row_and_column() {
            var layouts = [root.topDownLayout, root.bottomUpLayout, root.rightLeftLayout, root.offsetLayout];
            for (var layoutIndex = 0; layoutIndex < layouts.length; layoutIndex++) {
                var layout = layouts[layoutIndex];
                for (var rowIndex = 0; rowIndex < layout.rows; rowIndex++) {
                    for (var columnIndex = 0; columnIndex < layout.columns; columnIndex++) {
                        var workspaceId = OverviewWorkspaceMath.workspaceInCell(rowIndex, columnIndex, layout);
                        compare(OverviewWorkspaceMath.workspaceRow(workspaceId, layout), rowIndex);
                        compare(OverviewWorkspaceMath.workspaceColumn(workspaceId, layout), columnIndex);
                    }
                }
            }
        }
    }
}
