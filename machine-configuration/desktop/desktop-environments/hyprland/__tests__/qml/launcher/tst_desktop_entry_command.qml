import QtQuick
import QtTest
import "../../../../quickshell/bar/program-configuration/launcher/services/DesktopEntryCommand.js" as DesktopEntryCommand

TestCase {
    name: "DesktopEntryCommand"

    function test_literal_arguments_remain_shell_quoted() {
        compare(DesktopEntryCommand.joinShellArguments(["app", "a b", "$(touch /tmp/no)", "'", ""]), "'app' 'a b' '$(touch /tmp/no)' ''\"'\"'' ''");
    }

    function test_detached_entry_data() {
        return [
            {
                tag: "arguments",
                command: ["app", "a b"],
                directory: "",
                terminal: false,
                expected: "'app' 'a b'"
            },
            {
                tag: "exec-fallback",
                command: [],
                directory: "",
                terminal: false,
                expected: "app --argument"
            },
            {
                tag: "directory",
                command: ["app"],
                directory: "/a b",
                terminal: false,
                expected: "cd '/a b' && 'app'"
            },
            {
                tag: "terminal",
                command: ["app", "a b"],
                directory: "",
                terminal: true,
                expected: "'wezterm' 'start' '--' 'app' 'a b'"
            },
            {
                tag: "terminal-directory",
                command: ["app"],
                directory: "/a b",
                terminal: true,
                expected: "'wezterm' 'start' '--cwd' '/a b' '--' 'app'"
            },
            {
                tag: "terminal-exec-fallback",
                command: [],
                directory: "",
                terminal: true,
                expected: "'wezterm' 'start' '--' 'sh' '-lc' 'app --argument'"
            }
        ];
    }

    function test_detached_entry(data) {
        compare(DesktopEntryCommand.detachedLaunchCommand({
            command: data.command,
            execString: "app --argument",
            workingDirectory: data.directory,
            runInTerminal: data.terminal
        }), data.expected);
    }
}
