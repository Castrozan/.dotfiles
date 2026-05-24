# NVIDIA Policy

This module configures the NVIDIA proprietary driver for a Dell G15 5515 with AMD Renoir iGPU + NVIDIA RTX 3050 Ti dGPU. NixOS assertions enforce PRIME sync, modesetting, and LTS kernel pinning at evaluation time.


## PRIME Sync Topology

The Dell G15 5515 has a muxless hybrid GPU design where the laptop display is physically wired to the AMD iGPU (PCI 4:0:0). The NVIDIA dGPU (PCI 1:0:0) renders frames and copies them to the iGPU's framebuffer for scanout. PRIME sync mode keeps both GPUs in lockstep so every rendered frame reaches the display — without sync, the copy can race with the scanout causing visible tearing that no compositor can fix because it happens below the compositor layer.

PRIME offload is the alternative where the iGPU handles display and the dGPU only activates on demand. This saves power but introduces frame copy latency and requires applications to opt in via environment variables. For a workstation always plugged in, sync mode gives consistent full-GPU performance with zero per-application configuration.


## Modesetting and DRM

Kernel modesetting (`hardware.nvidia.modesetting.enable`) loads `nvidia_drm` with `modeset=1`. Wayland compositors (Hyprland, GNOME/Mutter) require DRM (Direct Rendering Manager) KMS to enumerate outputs, set display modes, and manage VT switching. Without modesetting, Wayland gets no DRM device and falls back to Xorg or fails entirely.

The four kernel modules (`nvidia`, `nvidia_modeset`, `nvidia_uvm`, `nvidia_drm`) are loaded in initrd to ensure the display is available before the display manager starts. Loading them later causes a race where GDM starts before the NVIDIA DRM device exists, producing a black screen for 5-10 seconds.


## Driver Pinning

The NVIDIA driver is pinned to 550.135 using `mkDriver` with explicit hashes for each component. The `nvidiaPackages` set in nixpkgs tracks upstream releases and may bump to a newer version that has not been validated against the current kernel. Pinning prevents surprise breakage after `nix flake update`.

The kernel is pinned to `linuxPackages_6_1` (LTS 6.1.x). NVIDIA 550.x is built and tested against 6.1 LTS — newer kernels change internal APIs (`struct drm_driver`, `vm_operations_struct`) that break the proprietary module build. When NVIDIA releases a driver validated for a newer kernel, both the kernel pin and driver pin should be updated together.


## Power Management

Power management is explicitly disabled (`powerManagement.enable = false`, `finegrained = false`). NVIDIA power management on Linux uses D3cold (PCIe power gating) which requires BIOS ACPI cooperation. The Dell G15 5515 BIOS does not properly support runtime D3 for the dGPU — enabling it causes the GPU to fail to wake from suspend, requiring a hard reboot. The GPU draws ~5W at idle which is acceptable for a plugged-in workstation.


## Performance Locking

A systemd oneshot service locks GPU clocks to 1500-2100 MHz core and 6001 MHz memory after `nvidia-persistenced` starts. Without this, the GPU dynamically clocks between 210-2100 MHz, causing microstutter when the clock ramps up during sudden load transitions (compositor effects, video decoding, CUDA launches). Persistence mode (`nvidia-smi -pm 1`) keeps the driver loaded even with no active clients, eliminating the 200ms cold-start latency when the first GPU application launches.


## Session Variables

`LIBVA_DRIVER_NAME=nvidia` routes VA-API video decode through the NVIDIA driver instead of the mesa fallback. `__GLX_VENDOR_LIBRARY_NAME=nvidia` ensures GLX uses the NVIDIA vendor library on the PRIME sync output. `GBM_BACKEND=nvidia-drm` tells GBM-based compositors (Hyprland) to use the NVIDIA allocator. `NVD_BACKEND=direct` configures the nvidia-vaapi-driver to use direct rendering rather than going through EGL.
