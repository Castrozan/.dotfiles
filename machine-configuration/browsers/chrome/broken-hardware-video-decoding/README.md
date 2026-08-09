# Chrome broken hardware video decoding

Chrome cannot decode video in hardware on a hybrid NVIDIA and AMD laptop, and it does not know that. It refuses the
NVIDIA render node outright, then fails on what is left with `failed Initialize()ing the frame pool` from
`media/gpu/vaapi/vaapi_video_decoder.cc` and tears the decoder down. This happens for every codec, H.264 included, so
accelerated decoding is already dead and every video is decoded in software regardless of this workaround.

The damage is that Chrome keeps advertising the capability it just failed to initialize. `canPlayType` still answers
`probably` for H.265, which is the one codec Chrome has no software decoder for. Jellyfin builds its client device
profile from that answer, concludes the browser can direct play HEVC, and serves the file untranscoded. The video
element then dies on `PIPELINE_ERROR_DECODE` while the web client surfaces no error, so an HEVC episode sits on a black
screen forever while an H.264 episode beside it plays normally.

Disabling accelerated video decode withdraws the claim, which drops H.265 out of `canPlayType` and lets Jellyfin
transcode to H.264 on the GPU encoder instead. It costs nothing, because the path it disables never initialized. The
two narrower flags that look like they should work, suppressing the platform HEVC decoder and suppressing the VA-API
decoder, were both measured and neither changes what `canPlayType` answers.

Wrapping the Chrome package rather than editing a launcher is what makes the flag hold. Chrome is started from more
than one entry point here, and each resolves the binary its own way, so a flag added to one launcher silently misses
the others. The wrapper covers every caller that resolves `google-chrome-stable`.

Delete this directory once Chrome initializes a VA-API frame pool on this hardware, or once a flag suppresses the H.265
claim without disabling the whole decode path. To retest, remove the wrapper and play an HEVC file in Jellyfin, then
read `error.message` off the video element.
