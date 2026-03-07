# Network Policy

This module configures TCP congestion control, WiFi power management, socket buffers, and encrypted network profiles. NixOS assertions enforce the critical invariants at evaluation time — a build fails before it can deploy a broken network stack.


## BBR and Fair Queue

BBR (Bottleneck Bandwidth and Round-trip propagation time) replaces CUBIC as the TCP congestion control algorithm. BBR estimates the actual delivery rate of the path rather than inferring congestion from packet loss. On lossy WiFi links where random drops are common, CUBIC misinterprets every drop as congestion and halves its window — BBR ignores non-congestion loss entirely.

BBR requires the `fq` (Fair Queue) qdisc as a hard dependency. BBR sends pacing information with each packet telling the kernel when to release the next one. Only `fq` honors these pacing instructions. With `fq_codel` or `pfifo_fast`, BBR's pacing metadata is ignored and it degrades to loss-based behavior functionally identical to CUBIC. The kernel does not enforce this pairing — it silently misbehaves. The NixOS assertion catches this.

The `tcp_bbr` kernel module must be loaded explicitly. The sysctl alone is not enough — the kernel needs the module present before it can select BBR as the congestion algorithm.


## WiFi Power Management

Power saving is disabled unconditionally. WiFi power management tells the radio to sleep between beacon intervals and wake on DTIM. On 5GHz DFS (Dynamic Frequency Selection) channels, the radio must perform radar detection during quiet periods mandated by regulatory rules. When the radio sleeps through a quiet period, the driver misses the detection window and the AP may force a channel switch or the client drops entirely. This manifests as random 2-5 second disconnects on channels 52-144.

Even on non-DFS channels, power save adds 100-500ms latency jitter because the client must wait for the next beacon to signal the AP that it is awake and ready to receive buffered frames. For a workstation that is always plugged in, there is zero benefit to WiFi power saving.


## Buffer Tuning

Socket buffer sizes are set to 16MB maximum and 1MB default for both send and receive. The 16MB maximum accommodates high-bandwidth transfers over paths with moderate RTT — the bandwidth-delay product of a 1Gbps link with 100ms RTT is 12.5MB, so 16MB provides headroom. The 1MB default is high enough for most flows without requiring application-level tuning, but low enough to avoid excessive memory consumption from idle connections.

TCP auto-tuning dynamically sizes each socket's buffer between the default and the maximum based on observed throughput. Setting only the maximum lets auto-tuning work correctly — it does not force every socket to allocate 16MB.

`tcp_fastopen` is enabled for both client (bit 0) and server (bit 1) to save one RTT on repeated connections. `tcp_slow_start_after_idle` is disabled so long-lived connections do not reset their congestion window after idle periods. `tcp_mtu_probing` discovers the path MTU to avoid fragmentation. `netdev_max_backlog` is raised to 16384 to prevent packet drops during traffic bursts on the receive side.


## Encrypted Network Profiles

The WiFi PSK is stored as an agenix-encrypted secret and injected at activation time through NetworkManager's `ensureProfiles.environmentFiles`. The profile definition references `$WIFI_PSK_ZANONI` which NetworkManager substitutes from the environment file. This keeps the PSK out of the Nix store and the git repository while still allowing fully declarative profile management.

The profile is pinned to band `a` (5GHz) to prefer the less congested spectrum and higher throughput. The `infrastructure` mode and `wpa-psk` key management are explicit to prevent NetworkManager from negotiating down.


## Dual-Platform Pattern

NixOS networking is configured here as a system-level module with declarative options. Ubuntu networking is handled separately through a home-manager activation script that writes NetworkManager dispatcher scripts and sysctl values, skipping when `/etc/NIXOS` exists. The two never overlap — the activation script's NixOS guard ensures this module is the single source of truth on NixOS hosts.
