import Quickshell.Io

Process {
    id: hardwareTemperaturesRoot

    required property string gpuType

    signal cpuTemperatureRead(real temperature)
    signal gpuTemperatureRead(real temperature)

    command: ["sensors"]
    environment: ({
            LANG: "C.UTF-8",
            LC_ALL: "C.UTF-8"
        })
    stdout: SplitParser {
        splitMarker: ""
        onRead: data => {
            let cpuTemp = data.match(/(?:Package id [0-9]+|Tdie):\s+((\+|-)[0-9.]+)(°| )C/);
            if (!cpuTemp)
                cpuTemp = data.match(/Tctl:\s+((\+|-)[0-9.]+)(°| )C/);

            if (cpuTemp)
                hardwareTemperaturesRoot.cpuTemperatureRead(parseFloat(cpuTemp[1]));

            if (hardwareTemperaturesRoot.gpuType !== "GENERIC")
                return;

            let eligible = false;
            let sum = 0;
            let count = 0;

            for (const line of data.trim().split("\n")) {
                if (line === "Adapter: PCI adapter")
                    eligible = true;
                else if (line === "")
                    eligible = false;
                else if (eligible) {
                    let match = line.match(/^(temp[0-9]+|GPU core|edge)+:\s+\+([0-9]+\.[0-9]+)(°| )C/);
                    if (!match)
                        match = line.match(/^(junction|mem)+:\s+\+([0-9]+\.[0-9]+)(°| )C/);

                    if (match) {
                        sum += parseFloat(match[2]);
                        count++;
                    }
                }
            }

            hardwareTemperaturesRoot.gpuTemperatureRead(count > 0 ? sum / count : 0);
        }
    }
}
