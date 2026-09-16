import Quickshell
import Quickshell.Io
import "AudioDeviceData.js" as AudioDeviceData

Scope {
    id: pulseAudioDiscoveryRoot

    required property var previousSinks
    required property var previousSources

    signal sinksDiscovered(var devices)
    signal sourcesDiscovered(var devices)
    signal defaultSinkNameDiscovered(string name)
    signal defaultSourceNameDiscovered(string name)
    signal cardsDiscovered(var cards)

    function refresh(): void {
        listSinksProcess.running = true;
        listSourcesProcess.running = true;
        getDefaultSinkProcess.running = true;
        getDefaultSourceProcess.running = true;
        listCardsProcess.running = true;
    }

    Process {
        id: listSinksProcess
        command: ["env", "LC_ALL=C", "pactl", "--format=json", "list", "sinks"]
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                try {
                    const parsed = JSON.parse(data);
                    const newSinks = parsed.map(sink => ({
                                index: sink.index,
                                name: sink.name,
                                description: sink.description ?? "",
                                mute: sink.mute ?? false,
                                volume: AudioDeviceData.extractVolumePercent(sink.volume),
                                state: sink.state ?? "",
                                portType: AudioDeviceData.extractPortType(sink.ports, sink.active_port),
                                isBluetooth: (sink.name ?? "").startsWith("bluez_")
                            }));
                    if (!AudioDeviceData.audioDeviceListsAreEqual(pulseAudioDiscoveryRoot.previousSinks, newSinks))
                        pulseAudioDiscoveryRoot.sinksDiscovered(newSinks);
                } catch (e) {}
            }
        }
    }

    Process {
        id: listSourcesProcess
        command: ["env", "LC_ALL=C", "pactl", "--format=json", "list", "sources"]
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                try {
                    const parsed = JSON.parse(data);
                    const newSources = parsed.filter(source => (source.name ?? "").indexOf(".monitor") === -1).map(source => ({
                                index: source.index,
                                name: source.name,
                                description: source.description ?? "",
                                mute: source.mute ?? false,
                                volume: AudioDeviceData.extractVolumePercent(source.volume),
                                state: source.state ?? "",
                                portType: AudioDeviceData.extractPortType(source.ports, source.active_port),
                                isBluetooth: (source.name ?? "").startsWith("bluez_")
                            }));
                    if (!AudioDeviceData.audioDeviceListsAreEqual(pulseAudioDiscoveryRoot.previousSources, newSources))
                        pulseAudioDiscoveryRoot.sourcesDiscovered(newSources);
                } catch (e) {}
            }
        }
    }

    Process {
        id: getDefaultSinkProcess
        command: ["pactl", "get-default-sink"]
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                pulseAudioDiscoveryRoot.defaultSinkNameDiscovered(data.trim());
            }
        }
    }

    Process {
        id: getDefaultSourceProcess
        command: ["pactl", "get-default-source"]
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                pulseAudioDiscoveryRoot.defaultSourceNameDiscovered(data.trim());
            }
        }
    }

    Process {
        id: listCardsProcess
        command: ["env", "LC_ALL=C", "pactl", "--format=json", "list", "cards"]
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                try {
                    const parsed = JSON.parse(data);
                    pulseAudioDiscoveryRoot.cardsDiscovered(parsed.map(card => {
                        const availableProfiles = [];
                        const profilesObject = card.profiles ?? {};
                        for (const profileName in profilesObject) {
                            const profile = profilesObject[profileName];
                            if (profile.available !== false && profileName !== "off")
                                availableProfiles.push({
                                    name: profileName,
                                    description: profile.description ?? profileName
                                });
                        }
                        return {
                            index: card.index,
                            name: card.name ?? "",
                            activeProfile: card.active_profile ?? "",
                            profiles: availableProfiles
                        };
                    }));
                } catch (e) {}
            }
        }
    }
}
