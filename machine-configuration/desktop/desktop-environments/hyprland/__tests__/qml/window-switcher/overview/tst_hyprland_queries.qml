import QtQuick
import QtTest
import "../../../../../quickshell/overview/program-configuration/services"

Item {
    HyprlandQueryProcesses {
        id: queries
    }

    TestCase {
        name: "HyprlandQueries"

        function clientsQuery() {
            return queries.children.find(query => query.command?.[1] === "clients");
        }

        function finish(query) {
            query.running = false;
            query.exited(0, 0);
        }

        function init() {
            queries.active = true;
        }

        function cleanup() {
            queries.active = false;
            for (const query of queries.children) {
                if (query.running)
                    finish(query);
            }
        }

        function test_busy_refresh_runs_once_after_completion() {
            const query = clientsQuery();
            queries.refresh(true, false, false, false, false);
            verify(query.running);
            for (let index = 0; index < 20; index++)
                queries.refresh(true, false, false, false, false);
            finish(query);
            verify(query.running);
            finish(query);
            verify(!query.running);
        }

        function test_closed_queries_ignore_refresh() {
            queries.active = false;
            queries.refresh(true, true, true, true, true);
            for (const query of queries.children)
                verify(!query.running);
        }

        function test_closing_discards_queued_refresh() {
            const query = clientsQuery();
            queries.refresh(true, false, false, false, false);
            queries.refresh(true, false, false, false, false);
            queries.active = false;
            finish(query);
            verify(!query.running);
        }

        function test_reopening_during_query_refreshes_after_completion() {
            const query = clientsQuery();
            queries.refresh(true, false, false, false, false);
            queries.active = false;
            queries.active = true;
            queries.refresh(true, false, false, false, false);
            finish(query);
            verify(query.running);
            finish(query);
            verify(!query.running);
        }

        function test_queries_coalesce_independently() {
            queries.refresh(true, true, true, true, true);
            queries.refresh(false, true, false, false, false);
            for (const query of queries.children) {
                finish(query);
                compare(query.running, query.command[1] === "monitors");
            }
        }
    }
}
