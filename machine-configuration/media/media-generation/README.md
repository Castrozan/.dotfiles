# File speech

`media-speech` generates narration through the same request contract using local Kokoro or ElevenLabs. It runs on demand and writes a mono, 24 kHz, 16-bit PCM WAV plus a JSON receipt under `$XDG_STATE_HOME/media-speech` (default `~/.local/state/media-speech`). The Python `SpeechService` consumes the domain-owned `SpeechProvider` protocol; provider SDKs and runtimes stay in adapters.

```sh
media-speech generate --provider kokoro --language pt-br --voice pf_dora \
  --text-file narration.txt
media-speech generate --provider elevenlabs --language pt-br --voice YOUR_VOICE_ID \
  --text-file narration.txt
media-speech inspect OPERATION_UUID
```

ElevenLabs reads an explicit `ELEVENLABS_API_KEY` environment value first, then the agenix-deployed `~/.secrets/elevenlabs-api-key` file. The shared secret declaration encrypts the credential for every configured host; plaintext stays outside the Nix store and repository. Obtain a voice available to your account; voice rights and account pricing require separate verification. Requests use Multilingual v2 and the [timestamp endpoint](https://elevenlabs.io/docs/api-reference/text-to-speech/convert-with-timestamps) with `pcm_24000`; automatic retries are disabled. Multilingual v2 does not support language enforcement through `language_code`, so verify the generated narration's language.

Kokoro runs the optimized INT8 export from [model-files-v1.0](https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0) with two CPU inference threads. The v1.1 release’s INT8 export uses a ConvInteger operator unsupported by the pinned CPU runtime; the model and voices are fetched independently with fixed hashes. Supported voices are `pf_dora`, `pm_alex`, `pm_santa` for `pt-br`, and `af_heart`, `af_bella`, `am_adam` for `en-us`. [Kokoro's model card](https://huggingface.co/hexgrad/Kokoro-82M) documents Apache-2.0 weights; the runtime and phonemizer have their own licenses. Nix supplies Python, ONNX Runtime, model files and eSpeak. The package uses Phonemizer 3.4; its Darwin-only dlinfo override excludes Linux filesystem tests that assume shared-cache system libraries exist as files. Imports and real synthesis validate the actual Darwin path.

The text limit is 4,000 characters. Supply `--operation-id` with a UUID to reuse a successful operation without generating again. The receipt verifies the audio checksum before replay. Changed requests conflict; interrupted or failed operations never dispatch again under that UUID. Inspect their receipts before starting another operation.

Receipts record measured audio metadata, provider identity, execution time, peak process memory and available usage evidence. ElevenLabs character alignment carries the provider's text and whether it matches the input. Kokoro reports alignment unavailable; caption timing needs a separate aligner. A local provider charge of zero excludes electricity and hardware. Cloud charges remain unknown, including on failure; reported character usage is not a dollar quote. This pilot does not enforce episode budgets or implement charge reconciliation, image/video generation, streaming or Shorts publishing.
