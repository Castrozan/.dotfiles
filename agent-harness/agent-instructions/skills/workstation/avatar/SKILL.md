---
name: avatar
description: "Control the local avatar, virtual meeting microphone and camera, speech, expressions, audio levels and video composition."
---

### Runtime

Use the installed `avatar-start`, `avatar-stop`, and `avatar-audio` commands on NixOS. The user services belong to
`avatar.target`; no meeting is joined by starting them. Inspect service state and the control server health endpoint
before reporting readiness. The renderer serves its model and libraries locally.

### Audio routing

`AvatarMic` accepts agent application audio; `AvatarMicrophone` is the mixed meeting input. Route only the intended
application stream, using its output selector or `PULSE_SINK=AvatarMic`. This does not expose an arbitrary voice
session's audio API. Human attachment is explicit; both input channels start muted. Never route meeting playback into
these inputs. Physical capture and meeting transmission need the user's applicable authorization.

### Camera

The renderer supports avatar, camera and composite modes. Physical camera access requires the local browser permission
flow first. `setVideoMode` acknowledges a request; wait for `videoModeChanged` or `videoModeError` for its result.
Start the virtual-camera producer before asking a meeting application to enumerate devices: exclusive-capability
v4l2loopback devices advertise capture only while a producer is attached.
