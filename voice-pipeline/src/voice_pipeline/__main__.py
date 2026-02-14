import argparse
import asyncio
import logging
import signal
import sys

from voice_pipeline.config import VoicePipelineConfig


def main() -> None:
    parser = argparse.ArgumentParser(description="Real-time voice pipeline")
    parser.add_argument("--agent", help="Default agent to use")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("toggle", help="Toggle pipeline on/off")

    agent_parser = subparsers.add_parser("agent", help="Switch agent")
    agent_parser.add_argument("name", help="Agent name")

    subparsers.add_parser("status", help="Query pipeline status")

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

    config = VoicePipelineConfig()
    if args.agent:
        config.default_agent = args.agent

    if args.command in ("toggle", "agent", "status"):
        asyncio.run(_run_client_command(args, config))
    else:
        asyncio.run(_run_daemon(config))


async def _run_client_command(args: argparse.Namespace, config: VoicePipelineConfig) -> None:
    from voice_pipeline.adapters.unix_control import UnixSocketControlClient

    client = UnixSocketControlClient(socket_path=config.socket_path)

    try:
        if args.command == "toggle":
            result = await client.send_command("toggle")
        elif args.command == "agent":
            result = await client.send_command("agent", {"name": args.name})
        elif args.command == "status":
            result = await client.send_command("status")
        else:
            print(f"Unknown command: {args.command}", file=sys.stderr)
            sys.exit(1)

        print(f"{result}")
    except ConnectionRefusedError:
        print("Voice pipeline is not running", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Voice pipeline is not running", file=sys.stderr)
        sys.exit(1)


async def _run_daemon(config: VoicePipelineConfig) -> None:
    from voice_pipeline.adapters.sounddevice_audio import SounddeviceCapture, SounddevicePlayback
    from voice_pipeline.adapters.silero_vad import SileroVad
    from voice_pipeline.adapters.openclaw_llm import OpenClawCompletion
    from voice_pipeline.adapters.openai_tts import OpenAITtsSynthesizer
    from voice_pipeline.adapters.unix_control import UnixSocketControlServer
    from voice_pipeline.domain.conversation import ConversationHistory
    from voice_pipeline.domain.wake_word import WakeWordDetector
    from voice_pipeline.domain.pipeline import VoicePipeline

    gateway_token = config.read_secret(config.gateway_token_file)
    openai_api_key = config.read_secret(config.openai_api_key_file)
    deepgram_api_key = config.read_secret(config.deepgram_api_key_file)

    capture = SounddeviceCapture(
        device=config.capture_device,
        sample_rate=config.sample_rate,
        frame_duration_ms=config.frame_duration_ms,
    )
    playback = SounddevicePlayback(sample_rate=24000)
    vad = SileroVad(model_path=config.vad_model_path, sample_rate=config.sample_rate)

    if config.stt_engine == "deepgram":
        from voice_pipeline.adapters.deepgram_stt import DeepgramStreamingTranscriber
        transcriber = DeepgramStreamingTranscriber(
            api_key=deepgram_api_key,
            sample_rate=config.sample_rate,
        )
    else:
        from voice_pipeline.adapters.openai_whisper_stt import OpenAIWhisperTranscriber
        transcriber = OpenAIWhisperTranscriber(
            api_key=openai_api_key,
            sample_rate=config.sample_rate,
        )

    completion = OpenClawCompletion(
        gateway_url=config.gateway_url,
        token=gateway_token,
        model=config.model,
    )
    synthesizer = OpenAITtsSynthesizer(api_key=openai_api_key)
    control = UnixSocketControlServer(socket_path=config.socket_path)

    wake_detector = WakeWordDetector(config.wake_words)
    conversation = ConversationHistory(max_turns=config.max_history_turns)

    pipeline = VoicePipeline(
        capture=capture,
        playback=playback,
        vad=vad,
        transcriber=transcriber,
        completion=completion,
        synthesizer=synthesizer,
        wake_word_detector=wake_detector,
        conversation=conversation,
        default_agent=config.default_agent,
        vad_threshold=config.vad_threshold,
        vad_min_silence_ms=config.vad_min_silence_ms,
        conversation_window_seconds=config.conversation_window_seconds,
        barge_in_enabled=config.barge_in_enabled,
        agent_voice_map=config.agent_voices,
    )

    loop = asyncio.get_event_loop()

    def handle_signal() -> None:
        logging.info("Received signal, shutting down...")
        asyncio.create_task(pipeline.stop())

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_signal)

    await control.start()

    async def control_loop() -> None:
        async for cmd in control.commands():
            if cmd.action == "toggle":
                pipeline.toggle()
            elif cmd.action == "agent" and cmd.payload:
                pipeline.switch_agent(cmd.payload.get("name", config.default_agent))
            elif cmd.action == "status":
                logging.info(
                    "Status: state=%s agent=%s enabled=%s",
                    pipeline.state.name,
                    pipeline.agent,
                    pipeline.enabled,
                )

    try:
        await asyncio.gather(
            pipeline.run(),
            control_loop(),
        )
    finally:
        await control.stop()


if __name__ == "__main__":
    main()
