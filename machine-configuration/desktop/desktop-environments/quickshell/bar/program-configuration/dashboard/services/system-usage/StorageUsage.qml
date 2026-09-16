import Quickshell.Io

Process {
    id: storageUsageRoot

    signal disksRead(var disks)

    command: ["lsblk", "-b", "-o", "NAME,SIZE,TYPE,FSUSED,FSSIZE", "-P"]
    stdout: SplitParser {
        splitMarker: ""
        onRead: data => {
            const diskMap = {};
            const lines = data.trim().split("\n");

            for (const line of lines) {
                if (line.trim() === "")
                    continue;

                const nameMatch = line.match(/NAME="([^"]+)"/);
                const sizeMatch = line.match(/SIZE="([^"]+)"/);
                const typeMatch = line.match(/TYPE="([^"]+)"/);
                const fsusedMatch = line.match(/FSUSED="([^"]*)"/);
                const fssizeMatch = line.match(/FSSIZE="([^"]*)"/);

                if (!nameMatch || !typeMatch)
                    continue;

                const name = nameMatch[1];
                const type = typeMatch[1];
                const size = parseInt(sizeMatch?.[1] || "0", 10);
                const fsused = parseInt(fsusedMatch?.[1] || "0", 10);
                const fssize = parseInt(fssizeMatch?.[1] || "0", 10);

                if (type === "disk") {
                    if (name.startsWith("zram"))
                        continue;

                    if (!diskMap[name])
                        diskMap[name] = {
                            name: name,
                            totalSize: size,
                            used: 0,
                            fsTotal: 0
                        };
                } else if (type === "part") {
                    let parentDisk = name.replace(/p?\d+$/, "");
                    if (name.match(/nvme\d+n\d+p\d+/))
                        parentDisk = name.replace(/p\d+$/, "");

                    if (diskMap[parentDisk]) {
                        diskMap[parentDisk].used += fsused;
                        diskMap[parentDisk].fsTotal += fssize;
                    }
                }
            }

            const diskList = [];
            for (const diskName of Object.keys(diskMap).sort()) {
                const disk = diskMap[diskName];
                const total = disk.fsTotal > 0 ? disk.fsTotal : disk.totalSize;
                const used = disk.used;
                const perc = total > 0 ? used / total : 0;

                diskList.push({
                    mount: disk.name,
                    used: used / 1024,
                    total: total / 1024,
                    free: (total - used) / 1024,
                    perc: perc
                });
            }

            storageUsageRoot.disksRead(diskList);
        }
    }
}
