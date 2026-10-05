# Private media generation

`media-speech` generates narration through the same request contract using local Kokoro or ElevenLabs. It runs on demand and writes a mono, 24 kHz, 16-bit PCM WAV plus a JSON receipt under `$XDG_STATE_HOME/media-speech` (default `~/.local/state/media-speech`). The Python `SpeechService` consumes the domain-owned `SpeechProvider` protocol; provider SDKs and runtimes stay in adapters.

```sh
media-speech providers
media-speech voices --provider kokoro
media-speech voices --provider elevenlabs --search Sarah
media-speech usage --provider kokoro
media-speech usage --provider elevenlabs
media-speech generate --help
media-speech generate --provider kokoro --language pt-br --voice pf_dora \
  --text-file narration.txt
media-speech generate --provider elevenlabs --language pt-br --voice YOUR_VOICE_ID \
  --text-file narration.txt
media-speech inspect OPERATION_UUID
```

`providers` returns the configured model, languages, text limit, payment and credential requirements, alignment capability, language enforcement and usage capabilities as JSON without loading an inference runtime or reading credentials. Usage capabilities name the status, scope and reported metrics. `voices` returns `voice_id`, name, known local language and any provider preview URL. Use the returned `voice_id` as `--voice`; the display name is not an identifier. `inspect` reads a local operation receipt.

`usage` calls the public `ProviderUsageService`, which consumes the domain-owned `ProviderUsageReader` port. Adapters translate vendor responses into the same snapshot contract; consumers use this API rather than provider SDKs. Each quota includes its name, unit, used amount, limit, remaining amount and reset time. Unknown values stay null, and `unavailable` differs from `not_applicable`. Snapshots include their observation time and account scope; they do not attribute account usage to this CLI or a particular machine.

ElevenLabs usage wraps the SDK's [Get user subscription API](https://elevenlabs.io/docs/api-reference/user/subscription/get), with a 30-second timeout and no retries. It reports credits, voice slots, plan/status and available overage charge/settings. Account quota is separate from an API key's configured spending cap; this query does not report that key cap. Kokoro reports `not_applicable` for subscription usage without reading credentials, loading model files or inferring zero compute cost. Neither usage query generates audio, creates operation state, changes account settings, reserves budget or checks balance before generation.

Voice discovery generates no audio and creates no operation receipt. Kokoro lists the bundled voices without model files. ElevenLabs reads the authenticated account catalog through the SDK's [List voices API](https://elevenlabs.io/docs/api-reference/voices/search), with a 30-second timeout and no retries. Each call reads one page; pass a returned `next_page_token` through `--page-token` with the same `--search` to continue. `--page-size` requests 1–100 results, default 20; ElevenLabs can include additional default voices on the first page. A cloud voice's `language` is null because the catalog does not establish language enforcement. Catalog membership is not a price quote or permission to use a particular voice.

ElevenLabs reads an explicit `ELEVENLABS_API_KEY` environment value first, then the agenix-deployed `~/.secrets/elevenlabs-api-key` file. The shared secret declaration encrypts the credential for every configured host; plaintext stays outside the Nix store and repository. Obtain a voice available to your account; voice rights and account pricing require separate verification. Requests use Multilingual v2 and the [timestamp endpoint](https://elevenlabs.io/docs/api-reference/text-to-speech/convert-with-timestamps) with `pcm_24000`; automatic retries are disabled. Multilingual v2 does not support language enforcement through `language_code`, so verify the generated narration's language.

Kokoro runs the optimized INT8 export from [model-files-v1.0](https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0) with two CPU inference threads. The v1.1 release’s INT8 export uses a ConvInteger operator unsupported by the pinned CPU runtime; the model and voices are fetched independently with fixed hashes. Supported voices are `pf_dora`, `pm_alex`, `pm_santa` for `pt-br`, and `af_heart`, `af_bella`, `am_adam` for `en-us`. [Kokoro's model card](https://huggingface.co/hexgrad/Kokoro-82M) documents Apache-2.0 weights; the runtime and phonemizer have their own licenses. Nix supplies Python, ONNX Runtime, model files and eSpeak. The package uses Phonemizer 3.4; its Darwin-only dlinfo override excludes Linux filesystem tests that assume shared-cache system libraries exist as files. Imports and real synthesis validate the actual Darwin path.

The text limit is 4,000 characters. Omitting `--operation-id` creates a new UUID, printed before dispatch and included in the result. Supply `--operation-id` with a UUID to reuse a successful operation without generating again. The receipt verifies the audio checksum before replay. Changed requests conflict; interrupted or failed operations never dispatch again under that UUID. Inspect their receipts before starting another operation.

Receipts record measured audio metadata, provider identity, execution time, peak process memory and available usage evidence. ElevenLabs character alignment carries the provider's text and whether it matches the input. Kokoro reports alignment unavailable; caption timing needs a separate aligner. A local provider charge of zero excludes electricity and hardware. Cloud charges remain unknown, including on failure; reported character usage is not a dollar quote. The speech API does not enforce episode budgets or implement charge reconciliation, streaming or Shorts publishing.

## Native video recipes

`media-video` renders a trusted, precompiled fframes recipe on demand. Nix supplies Python and FFmpeg for verification; the consumer supplies the native executable, source and assets. The `VideoService` library consumes the domain-owned `VideoRenderProvider` protocol, and `FframesRenderer` adapts the native executable. There is no network listener, recipe compiler or generative provider call.

```sh
media-video render --request-file /absolute/private/request.json
media-video inspect OPERATION_UUID
media-video --state-directory /absolute/private/state inspect OPERATION_UUID
```

State lives under `$XDG_STATE_HOME/media-video`, default `~/.local/state/media-video`. Each canonical UUID claims one private operation directory. The API retains request and registration JSON, checksum-verified input copies, the executable, process logs, MP4, PNG thumbnail and receipt. Receipts move from `dispatching` to `succeeded` or `failed`; successful replay verifies retained inputs and artifacts before returning the same receipt. Changed requests conflict. Failed, interrupted or incomplete operations cannot redispatch under their UUID. Inspect first, then explicitly choose a new UUID if another render is wanted.

The request JSON contains these fields; replace the paths and attribution with the consumer's values:

```json
{
  "operation_id": "1af70da8-a31b-4aeb-acb7-3418993c15bc",
  "recipe_registration": "/absolute/private/registration.json",
  "experiment_id": "shorts",
  "episode_id": "ice-cream",
  "width": 1080,
  "height": 1920,
  "fps": 30,
  "frames": 1800,
  "deadline_seconds": 600
}
```

The supported output is a 60-second vertical MP4: 1080 by 1920 pixels, 30 fps, exactly 1800 frames, with audio. The finite deadline covers preflight, input retention, rendering and verification and cannot exceed 600 seconds. Verification checks every frame timestamp, fully decodes audio and video, and checks thumbnail dimensions before syncing artifacts and atomically publishing a successful receipt. Container duration may exceed the 60-second video stream by at most 100 ms.

Registration JSON contains exactly `recipe_id`, `recipe_directory`, `renderer_version`, `binary` and `source_assets_manifest`. The recipe ID accepts letters, digits, hyphens and underscores, up to 100 characters. `renderer_version` identifies the consumer's compiled version. Both pinned file fields contain an absolute `path` and lowercase 64-character `sha256`. The source/assets manifest contains exactly `files`, a list of 1 to 512 entries with canonical relative `path` and `sha256`. Include every source and runtime asset needed by the executable. Combined binary, manifest and asset size is limited to 2 GiB.

Registration and manifest files require private modes, and their containing directories and the recipe directory require mode 0700. Inputs must be owned regular files with canonical paths; symlinks, traversal, duplicate JSON keys and duplicate manifest paths are refused. The native executable must be owned, executable and checksum-pinned. It must accept `render -o ABSOLUTE_OUTPUT_MP4` from the retained recipe working directory and use the copied assets there. An executable's native header and checksum establish its recorded identity, not a sandbox: register only trusted recipes. The consumer must supply a binary compatible with the target host and its runtime libraries. The service does not install or build fframes, fonts or recipes.

Rendering and verification run without a shell, with private bounded logs and process-group cleanup on timeout or interruption. Source/assets remain with the consumer; editorial timing, image generation, voice selection and browser publishing stay outside the renderer. Receipts report zero generative calls for the local render and leave compute cost unknown. They do not include previous image or narration charges.
