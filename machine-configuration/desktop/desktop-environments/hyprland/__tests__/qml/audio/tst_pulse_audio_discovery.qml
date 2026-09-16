import QtQuick
import QtTest
import "../../../../quickshell/bar/program-configuration/dashboard/services/audio"

Item {
    PulseAudioDiscovery {
        id: discovery
        previousSinks: []
        previousSources: []
        onSinksDiscovered: devices => previousSinks = devices
        onSourcesDiscovered: devices => previousSources = devices
    }
    TestCase {
        name: "PulseAudioDiscovery"
        function process(commandText) {
            for (const candidate of discovery.children)
                if (candidate.command.join(" ") === commandText)
                    return candidate;
            fail("Missing discovery process: " + commandText);
        }
        function init() {
            discovery.previousSinks = [];
            discovery.previousSources = [];
        }
        function test_sink_properties_and_defaults() {
            process("env LC_ALL=C pactl --format=json list sinks").stdout.read(JSON.stringify([
                {
                    index: 3,
                    name: "bluez_output.headset",
                    volume: {
                        left: {
                            value_percent: "81%"
                        }
                    },
                    ports: [
                        {
                            name: "headphones",
                            type: "Headset"
                        }
                    ],
                    active_port: "headphones"
                }
            ]));
            compare(discovery.previousSinks, [
                {
                    index: 3,
                    name: "bluez_output.headset",
                    description: "",
                    mute: false,
                    volume: 81,
                    state: "",
                    portType: "Headset",
                    isBluetooth: true
                }
            ]);
        }
        function test_monitor_sources_are_filtered() {
            process("env LC_ALL=C pactl --format=json list sources").stdout.read(JSON.stringify([
                {
                    index: 1,
                    name: "speaker.monitor"
                },
                {
                    index: 2,
                    name: "microphone"
                }
            ]));
            compare(discovery.previousSources.length, 1);
            compare(discovery.previousSources[0].name, "microphone");
        }
        function test_unchanged_devices_retain_list_identity() {
            const parser = process("env LC_ALL=C pactl --format=json list sinks").stdout;
            parser.read('[{"index":1,"name":"speaker"}]');
            const previous = discovery.previousSinks;
            parser.read('[{"index":1,"name":"speaker"}]');
            verify(previous === discovery.previousSinks);
        }
        function test_invalid_json_preserves_devices() {
            discovery.previousSinks = [
                {
                    name: "known"
                }
            ];
            process("env LC_ALL=C pactl --format=json list sinks").stdout.read("invalid");
            compare(discovery.previousSinks, [
                {
                    name: "known"
                }
            ]);
        }
        function test_refresh_starts_every_discovery_process() {
            for (const candidate of discovery.children)
                candidate.running = false;
            discovery.refresh();
            compare(discovery.children.length, 5);
            for (const candidate of discovery.children)
                verify(candidate.running);
        }
    }
}
