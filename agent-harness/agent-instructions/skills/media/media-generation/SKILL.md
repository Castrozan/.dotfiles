---
name: media-generation
description: Generate images, speech, narration and finished movies through the personal media API. Use for provider discovery, voice selection, expressive delivery, scene scripts and durable media jobs.
---

### Public boundary

Use `media-image`, `media-speech`, `media-movie` and `media-video` as the consumer boundary. Read their help and discovery
output for supported controls; read `media-movie schema` for scene inputs. Keep provider SDKs and credentials inside
adapters. Agent harnesses can call these APIs, but harness subscriptions do not establish provider API billing.

### Production ownership

The movie API assembles explicit scenes into an MP4; the directing pipeline owns scripts, editorial judgment and quality
acceptance. Select the native video API for trusted compiled compositions. Read [integration limits](knowledge.md) before
choosing between these paths.

### Partial jobs

Use the user's generation scope and budget. Account usage snapshots are observations, not reservations. Inspect failed
or interrupted operations and their child receipts before selecting another UUID; a new parent operation can charge
again for assets that the failed operation already generated.
