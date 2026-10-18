# RTX 3050 firmware resume failure

## Incident

On 2026-10-17 at 20:41:09 -03:00, Chise's RTX 3050 Laptop GPU reported a GPU System Processor (GSP) firmware
exception during GPU power-management resume. The loaded software observed during the 2026-10-18 investigation was
Linux 6.12.80 and NVIDIA 580.178.04 with the open kernel module.

The driver could not reinitialize GSP and marked the GPU as requiring a reset. The Quickshell GPU row displays `N/A`
because NVIDIA no longer returns numeric utilization. The fault predates the GPU row's addition to the bar.

## Evidence

The kernel recorded these messages at the incident time:

```text
NVRM: Xid (PCI:0000:01:00): 120, GSP task exception: environment call from U-mode (cause:0x8) @ pc:0x1a9cc98, partition:2#0, task:3
NVRM: gpuPowerManagementResume: GSP boot failed at resume (bootMode 0x1): 0x62
NVRM: Xid (PCI:0000:01:00): 154, GPU recovery action changed from 0x0 (None) to 0x1 (GPU Reset Required)
```

During the investigation, `nvidia-smi` continued to report `[GPU requires reset]` for performance state and temperature,
and `[N/A]` for GPU utilization. Quickshell remained active and displayed CPU and RAM readings.

[NVIDIA's Xid catalog](https://docs.nvidia.com/deploy/xid-errors/analyzing-xid-catalog.html) identifies Xid 120 as a GSP
error and lists GPU reset as a recovery action. The local log establishes a failure during GPU resume, but does not
identify the triggering workload or prove a particular driver defect or physical hardware damage. Whole-system suspend
was not established.

## Recovery and verification

As of the 2026-10-18 investigation, the owner plans to reboot when convenient. No GPU reset or reboot was performed
during the investigation. Recovery and recurrence remain unverified.

After that reboot, query the loaded driver and GPU readings:

```sh
nvidia-smi \
  --query-gpu=name,driver_version,pstate,utilization.gpu,temperature.gpu \
  --format=csv,noheader,nounits
```

Check only the current boot for recurrence:

```sh
journalctl -k -b --grep='NVRM.*Xid|GSP boot failed|GPU recovery action' --no-pager
```

Recovery requires numeric utilization and temperature, a performance state without the reset error, and a percentage
in the Quickshell GPU row. Check for new Xid 120 or 154 messages after the GPU idles and resumes again. A successful
boot alone does not establish that the resume failure is fixed. Record the post-reboot kernel and driver versions,
readings, and any recurrence before closing this incident.
