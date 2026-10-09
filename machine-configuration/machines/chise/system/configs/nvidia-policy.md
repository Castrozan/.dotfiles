# NVIDIA policy

Chise has an AMD integrated GPU and an NVIDIA RTX 3050 Laptop GPU. `nvidia.nix` owns its kernel, driver, PCI routing,
and compositor device selection. The production driver comes from the locked nixpkgs input and the selected kernel's
package set, so the kernel module and NVIDIA userspace share a driver release. The open NVIDIA kernel module supports
this Ampere GPU; it is separate from Nouveau and Mesa NVK.

### Hyprland routing

`AQ_DRM_DEVICES` selects NVIDIA as Hyprland's primary renderer and retains AMD for outputs connected to AMD. PRIME
sync controls Xorg and does not select Hyprland's renderer. Xorg uses PRIME offload with the native `nvidia-offload`
command available for applications that need NVIDIA explicitly.

The udev aliases bind DRM card nodes to PCI devices. Numeric `cardN` names can change at boot, and PCI paths containing
colons cannot appear directly in the colon-separated `AQ_DRM_DEVICES` list. Keep both aliases consistent with the
host's PCI bus IDs. See https://wiki.hypr.land/configuring/extra/multi-gpu/.

### Workload boundaries

Do not force GLX, GBM, or VA-API vendors globally. Applications that require a particular GPU must select it in their
own launch environment. CUDA and NVENC use NVIDIA independently of the compositor's display routing. Chrome's
hardware video decoding workaround remains until playback evidence supports removing it.

### Deployment and verification

Deploy kernel, driver, and routing changes together as a boot generation. Keep the running generation intact until a
user-authorized reboot. Before accepting the new generation, verify the loaded kernel and driver, both DRM aliases,
Hyprland's NVIDIA renderer, connected displays, Chrome WebGL and playback, and CUDA/NVENC workloads. A source review
or successful build does not establish runtime stability. Preserve the previous generation for recovery.
