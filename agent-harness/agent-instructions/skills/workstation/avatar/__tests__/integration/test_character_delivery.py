from control_server_node_runner import evaluate_node_json, requires_node
from character_voice_fixtures import (
    CHARACTER_VOICED_GENERATOR,
    CHARACTER_REQUEST_SESSION,
)


@requires_node
def test_character_voice_commits_only_after_renderer_success():
    result = evaluate_node_json(
        CHARACTER_VOICED_GENERATOR
        + CHARACTER_REQUEST_SESSION
        + """
        const { routeClientMessage } = require("./avatar-session/client-connection-router");
        Object.assign(context.clientRegistry, {
          isSeat: () => false, isAgent: () => false, isRenderer: () => true,
          sendToAgents: () => {}, connectionSummary: () => ({}),
        });
        context.speechFloor = { currentPhase: () => "idle" };
        const result = (async () => {
          request("second", "failed");
          await routeClientMessage(JSON.stringify({type: "characterError", id: "failed"}), connection, context);
          const afterError = spokenVoice();
          request("second", "success");
          await routeClientMessage(JSON.stringify({type: "characterChanged", name: "second", id: "success"}), connection, context);
          const { handleGetStatusCommand } = require("./agent-commands/get-status-command-handler");
          await handleGetStatusCommand({}, connection, context);
          return {afterError, afterSuccess: spokenVoice(), character: sent.at(-1).currentCharacter};
        })();
        """
    )
    assert result == {
        "afterError": "firstCloud",
        "afterSuccess": "secondCloud",
        "character": "second",
    }


@requires_node
def test_selected_models_reach_existing_meeting_speech_without_unsupported_directions():
    result = evaluate_node_json(
        """
        const requests = [];
        const clientPath = require.resolve("./speech/media-speech-client");
        require.cache[clientPath] = {exports: {runMediaSpeech: async args => {
          requests.push(args); return {audio: {path: "/test.wav", duration_seconds: 1}, alignment: {status: "unavailable"}};
        }}};
        const { ElevenLabsSpeechGenerator } = require("./speech/elevenlabs-speech-generator");
        const { ResilientSpeechGenerator } = require("./speech/resilient-speech-generator");
        const { CharacterVoicedSpeechGenerator } = require("./speech/character-voiced-speech-generator");
        const speech = new CharacterVoicedSpeechGenerator(
          new ResilientSpeechGenerator(new ElevenLabsSpeechGenerator("default", "en-us"), {}, {}),
          [{name: "first", cloudVoice: "voice", localVoice: "pf_first"}],
        );
        const result = (async () => {
          for (const model of ["eleven_turbo_v2_5", "eleven_flash_v2_5", "eleven_multilingual_v2"])
            await speech.generate("test", "turn", null, "neutral", model);
          return requests.map(args => ({model: args[args.indexOf("--model") + 1], directions: args.includes("--directions"), voice: args[args.indexOf("--voice") + 1]}));
        })();
        """
    )
    assert result == [
        {"model": model, "directions": False, "voice": "voice"}
        for model in (
            "eleven_turbo_v2_5",
            "eleven_flash_v2_5",
            "eleven_multilingual_v2",
        )
    ]
