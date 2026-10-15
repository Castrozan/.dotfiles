# Chrome AMD hardware video decoding

Chise's Chrome uses an AMD Mesa driver selected for the browser process. EGL, DRI, VA-API and the GBM backend must
come from the same Mesa package. Selecting a newer video driver while retaining an older GBM backend can crash the
GPU process before playback begins.

Chrome 147 with the system Mesa 25.2.6 reached AMD's hardware decoder but failed to import its BGRA frame buffers.
The browser logged `gbm_bo_import` and `CreateSharedImage` failures, then restarted its GPU process. An isolated
native Wayland test with a coherent Mesa 26.0.4 selection completed H.264 and HEVC playback without those errors.

The common Linux package selector applies this driver selection only to chise. It preserves native Wayland and the
separate ANGLE mipmap workaround, and leaves the desktop's driver and NVIDIA offload configuration unchanged. The
desktop entry, ordinary executable and Hyprland launcher resolve the same package.

Hardware decoding remains codec-dependent. This AMD GPU advertises H.264, HEVC and VP9 decoding, but no AV1
decoding. Verify the actual codec and decoder when assessing YouTube resource use. HEVC capability advertising is
accepted only when real HEVC playback succeeds; a `canPlayType` result alone is insufficient.

Chromium's Linux VA-API documentation describes the decoder and its verification:
https://chromium.googlesource.com/chromium/src/+/HEAD/docs/gpu/vaapi.md
