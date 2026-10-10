### Production ownership

Direct one original faceless Short for the channel in `config.json`. Read `shorts-production history` to include topics
reserved after this run's snapshot. Paraphrases of a previous subject and mechanism are the same idea. Reserve a genuinely
new topic once with `shorts-production reserve --episode-file episode.json` before generation.

### Research and learning

Retain dated source findings and three inspected reference Shorts. Compare views relative to channel size and release
age, three candidate topics, their viewer payoff and factual boundaries. Use at least one primary factual source. Inspect
prior public releases at day 1, day 7 and day 28 when due; save dated performance snapshots and use available retention
evidence to revise the next choice. Missing Studio analytics remain unknown; owner playback checks are not organic views.

### Style and voice

Choose any original faceless style supported by research. Build visual explanations, character action, demonstrations or
changes of scale that advance the story. Use original vector/code animation or assets with recorded rights. Paid image
and video calls are disabled until a separate measured budget is authorized. Use the private `media-video` interface for
registered native compositions; inspect installed help and contract. Compile native compositions for Linux on Chise.

Chise's prepared SDK and native example are under `~/clawde/shorts/native-kit`. Read the example's Cargo manifest,
source and registration before creating a composition in this run. Keep the pinned SDK unchanged. Use its built-in
CPU renderer with an MPEG4 intermediate, then encode the final H264/yuv420p video with installed FFmpeg.

Discover the live voice contract using `media-speech providers`, `voices` and `usage`. Direct an expressive American
ElevenLabs performance with curiosity, surprise, tension and humor where earned. Save usage before and after and the
operation receipt. Do not enable overage or retry before inspecting an incomplete operation. Review the complete
narration using available listening, transcript, timing and acoustic evidence. Record which checks actually ran;
claim direct listening only when an audio-capable tool supplied audio you inspected. Tags and a passing transcript
alone do not prove an entertaining voice; distinguish measured delivery from subjective quality that remains unknown.

### Editorial and media acceptance

Keep the final video at or below 25 MiB, PinchTab's per-file upload ceiling. Re-encode before verification if necessary;
the quality gate rejects oversized files before publication dispatch.

Write `episode.json` with `topic_key`, `title`, specific `summary`, relative `video`, three `candidates`, `sources` and
`references`. Each source/reference contains `url` and substantive `finding`; factual primary sources set `primary` to
true. Supply 6 to 24 `beats`, each with an inspected relative `frame` file. Align readable mobile captions and visuals
to the narration; keep claims synchronized with their demonstrations.

Supply `review` entries for `novel_topic`, `factual_accuracy`, `opening`, `payoff`, `visual_storytelling`,
`voice_performance`, `caption_readability`, `sound_mix` and `full_playback`. Each has `passed`, substantive `finding` and
relative `evidence`. Save actual frame inspection, narration review and browser-playback observations with their limits.
Record playback duration and errors.
Repair a failure or hold. Run `shorts-production verify --episode-file episode.json` and preserve its final video hash.

### Browser lifecycle

The existing systemd timer starts each production job at 09:00, 15:00 and 21:00 in America/Sao_Paulo.
The job requires the dedicated headless browser; the browser stops when no job needs it, including after failure,
timeout or cancellation. Between jobs only the timer remains. Keep the persistent profile data and never enable
`shorts-browser.service` at graphical login. Run-owned pages are reused and cleaned before the browser shuts down.

### Publishing boundary

Use `shorts-browser` for YouTube Studio; it binds every action to the existing dedicated profile identified by
`browser_profile` and `browser_profile_id` in `config.json`. It refuses profile management and endpoint overrides.
Its active channel must exactly match `config.json` before upload. Read the browser skill's unattended procedure;
use fresh snapshots and file upload. Never copy shared Chrome cookies or change another person's open tab.
Check publisher access before generating assets. If sign-in is needed, write the precise hold reason.

The launcher requires `~/clawde/shorts/publisher-ready.json` with `status` set to `ready` and matching `channel_id` and
`browser_profile` and `browser_profile_id`. Setup writes this record after verifying channel, upload and analytics UI.
Scheduled production agents must not create or change it; each still checks live access before generation and upload.

Run `shorts-production dispatch --episode-file episode.json` before uploading. An existing journal forbids an automatic
second dispatch. Complete Studio checks, source description and truthful audience/synthetic-content declarations before
publishing. Save the displayed direct video URL as `url` in `episode.json`.
Use `shorts-browser upload final.mp4 --tab TAB_ID --selector 'input[type=file]'` for the observed Studio input.
The adapter preserves MP4 filename and MIME through PinchTab's sandbox-path API. After confirmed publication,
remove only the returned `staged_file` and its empty staging directory; retain the original video in this run.
Run `shorts-production complete --episode-file episode.json`; anonymous metadata must prove exact channel and public
visibility. Inspect Studio and the journal after a timeout or ambiguous result before doing anything further.

### Failure and handoff

Keep research, receipts and artifacts inside this run. Write `hold.json` with the precise failed gate or unavailable
dependency and do not claim publication. A slot is claimed once, runs do not overlap, and missed slots are not backfilled.
This fresh scheduled session ends after one attempt. Do not edit dotfiles or launch extra agent sessions to finish it.

### Explicit recovery

An operator may enqueue inspected held slots using `shorts-production queue-recovery --run-id YYYY-MM-DD-HH00`.
The queue refuses an existing publication dispatch and preserves the original topic reservation. Run
`shorts-production drain-recovery` in a transient user service to process only those requested slots in sequence.
Each attempt archives the prior hold and agent evidence, uses the same production lock and headless browser, and
stops on a fresh hold. Recovery reserves the full job deadline before the next ordinary slot and gives the timer's
activation window priority. The normal timer never backfills automatically.
