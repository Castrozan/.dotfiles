{
  config,
  lib,
  pkgs,
  ...
}:
let
  cfg = config.services.hey-bot;

  keywordsPattern = builtins.concatStringsSep "|" cfg.keywords;

  heyBotDaemon = pkgs.writeShellApplication {
    name = "hey-bot";
    runtimeInputs = with pkgs; [
      sox
      whisper-cpp
      python3Packages.edge-tts
      mpv
      curl
      jq
      libnotify
      pipewire
    ];
    text = ''
      readonly WHISPER_MODEL="${cfg.whisperModel}"
      readonly KEYWORDS_PATTERN="${keywordsPattern}"
      readonly GATEWAY_URL="${cfg.gatewayUrl}"
      readonly GATEWAY_TOKEN_FILE="${cfg.gatewayTokenFile}"
      readonly AGENT_ID="${cfg.agentId}"
      readonly TTS_VOICE="${cfg.ttsVoice}"
      readonly MODEL="${cfg.model}"
      readonly TRANSCRIPTION_DIR="${cfg.transcriptionDir}"
      readonly MAX_LOG_SIZE=${toString cfg.maxLogFileSize}
      readonly CHUNK_DURATION=6
      readonly STEP_INTERVAL=4
      readonly COMMAND_COLLECTION_CHUNKS=3
      readonly ENERGY_THRESHOLD=0.02

      COMMAND_MODE=false
      COMMAND_CHUNKS_REMAINING=0
      COMMAND_BUFFER=""
      KEYWORD_PHRASE=""
      PREV_CHUNK=""
      PREV_REC_PID=""
      GATEWAY_TOKEN=""

      main() {
        mkdir -p "$TRANSCRIPTION_DIR"
        _load_gateway_token
        trap '_cleanup_background_jobs' EXIT
        echo "hey-bot: listening for keywords matching: $KEYWORDS_PATTERN"
        _recording_loop
      }

      _load_gateway_token() {
        if [[ -f "$GATEWAY_TOKEN_FILE" ]]; then
          GATEWAY_TOKEN=$(cat "$GATEWAY_TOKEN_FILE")
        fi
      }

      _cleanup_background_jobs() {
        jobs -p 2>/dev/null | xargs -r kill 2>/dev/null || true
      }

      _recording_loop() {
        while true; do
          local chunkFile
          chunkFile=$(mktemp /tmp/hey-bot-XXXXXX.wav)
          rec -q "$chunkFile" rate 16k channels 1 trim 0 "$CHUNK_DURATION" 2>/dev/null &
          local recPid=$!
          local iterationStart=$SECONDS

          if [[ -n "$PREV_REC_PID" ]]; then
            wait "$PREV_REC_PID" 2>/dev/null || true
          fi

          if [[ -n "$PREV_CHUNK" ]]; then
            _process_chunk "$PREV_CHUNK"
          fi

          PREV_REC_PID=$recPid
          PREV_CHUNK="$chunkFile"

          local elapsed=$((SECONDS - iterationStart))
          local sleepTime=$((STEP_INTERVAL - elapsed))
          if [[ $sleepTime -gt 0 ]]; then
            sleep "$sleepTime"
          fi
        done
      }

      _process_chunk() {
        local chunkFile="$1"

        if ! _chunk_has_audio "$chunkFile"; then
          rm -f "$chunkFile"
          _count_command_chunk_if_active
          return
        fi

        local transcription
        transcription=$(_transcribe_chunk "$chunkFile")
        rm -f "$chunkFile"

        if [[ -z "$transcription" ]]; then
          _count_command_chunk_if_active
          return
        fi

        local wordCount
        wordCount=$(echo "$transcription" | wc -w)

        if [[ "$wordCount" -ge 3 ]]; then
          _log_transcription "$transcription"
        fi

        if [[ "$COMMAND_MODE" == "true" ]]; then
          COMMAND_BUFFER="$COMMAND_BUFFER $transcription"
          _finish_command_chunk
          return
        fi

        if echo "$transcription" | grep -qiE "$KEYWORDS_PATTERN"; then
          _activate_command_mode "$transcription" "$wordCount"
          return
        fi
      }

      _chunk_has_audio() {
        local chunkFile="$1"
        local maxAmplitude
        maxAmplitude=$(sox "$chunkFile" -n stat 2>&1 | awk '/Maximum amplitude/ {print $3}')
        [[ -n "$maxAmplitude" ]] && awk "BEGIN {exit ($maxAmplitude < $ENERGY_THRESHOLD)}"
      }

      _transcribe_chunk() {
        local chunkFile="$1"
        whisper-cli -m "$WHISPER_MODEL" -f "$chunkFile" -nt -np -l auto --suppress-nst 2>/dev/null \
          | tr '\n' ' ' | sed 's/^ *//;s/ *$//;s/  */ /g' \
          | sed 's/\[BLANK_AUDIO\]//g; s/\[silence\]//gi; s/\[Music\]//gi; s/(humming)//gi; s/(singing)//gi' \
          | sed 's/^ *//;s/ *$//'
      }

      _count_command_chunk_if_active() {
        if [[ "$COMMAND_MODE" == "true" ]]; then
          _finish_command_chunk
        fi
      }

      _activate_command_mode() {
        local transcription="$1"
        local wordCount="$2"

        echo "hey-bot: keyword detected in: '$transcription'"
        if [[ "$wordCount" -lt 3 ]]; then
          _log_transcription "$transcription"
        fi
        notify-send "Hey Bot" "Listening..." 2>/dev/null || true

        COMMAND_MODE=true
        COMMAND_CHUNKS_REMAINING=$COMMAND_COLLECTION_CHUNKS
        KEYWORD_PHRASE="$transcription"
        COMMAND_BUFFER=""
      }

      _finish_command_chunk() {
        COMMAND_CHUNKS_REMAINING=$((COMMAND_CHUNKS_REMAINING - 1))
        if [[ "$COMMAND_CHUNKS_REMAINING" -le 0 ]]; then
          COMMAND_MODE=false
          if [[ -n "$COMMAND_BUFFER" ]]; then
            local fullCommand="$KEYWORD_PHRASE $COMMAND_BUFFER"
            fullCommand=$(echo "$fullCommand" | sed 's/^ *//;s/ *$//;s/  */ /g')
            echo "hey-bot: sending command to gateway in background"
            _process_command "$fullCommand" &
          else
            echo "hey-bot: empty command, returning to listening"
          fi
          COMMAND_BUFFER=""
          KEYWORD_PHRASE=""
        fi
      }

      _process_command() {
        local commandText="$1"
        commandText=$(echo "$commandText" | sed 's/^ *//;s/ *$//;s/  */ /g')

        echo "hey-bot: command: '$commandText'"
        _log_transcription "[COMMAND] $commandText"
        notify-send "Hey Bot" "$commandText" 2>/dev/null || true

        local responseText
        responseText=$(_send_to_gateway "$commandText")

        echo "hey-bot: response: '$(echo "$responseText" | head -c 200)'"
        _log_transcription "[RESPONSE] $responseText"

        if [[ "$responseText" == "IGNORE" ]]; then
          echo "hey-bot: nonsensical input, skipping TTS"
          return
        fi

        _speak_response "$responseText"
      }

      _send_to_gateway() {
        local commandText="$1"
        local recentTranscription
        recentTranscription=$(tail -20 "$(_get_log_file)" 2>/dev/null || echo "")

        curl -s --max-time 120 "$GATEWAY_URL/v1/chat/completions" \
          -H "Content-Type: application/json" \
          -H "Authorization: Bearer $GATEWAY_TOKEN" \
          -H "x-clawdbot-agent-id: $AGENT_ID" \
          -d "$(jq -n \
            --arg text "$commandText" \
            --arg model "$MODEL" \
            --arg agent "$AGENT_ID" \
            --arg context "$recentTranscription" \
            '{
              model: $model,
              user: ("voice-" + $agent),
              messages: [{
                role: "user",
                content: ("[Voice input from microphone transcription. Respond concisely for TTS playback. Match spoken language (English or Portuguese). If the transcription is nonsensical, garbled, or clearly not directed at you, respond with exactly IGNORE and nothing else.]\n\n[Recent ambient transcription for context:]\n" + $context + "\n\n[Command:]\n" + $text)
              }]
            }')" | jq -r '.choices[0].message.content // "Sorry, I could not process that."'
      }

      _speak_response() {
        local responseText="$1"
        local ttsFile
        ttsFile=$(mktemp /tmp/hey-bot-tts-XXXXXX.mp3)
        if edge-tts --text "$responseText" --voice "$TTS_VOICE" --write-media "$ttsFile" 2>/dev/null; then
          wpctl set-mute @DEFAULT_AUDIO_SINK@ 0 2>/dev/null || true
          mpv --no-video --ao=pipewire "$ttsFile" 2>/dev/null || true
        fi
        rm -f "$ttsFile"
      }

      _get_log_file() {
        local currentLogFile="$TRANSCRIPTION_DIR/current.log"
        if [[ -f "$currentLogFile" ]] && [[ $(stat -c%s "$currentLogFile") -gt $MAX_LOG_SIZE ]]; then
          mv "$currentLogFile" "$TRANSCRIPTION_DIR/$(date +%Y-%m-%d_%H-%M-%S).log"
        fi
        echo "$currentLogFile"
      }

      _log_transcription() {
        local transcriptionText="$1"
        local logFile
        logFile=$(_get_log_file)
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] $transcriptionText" >> "$logFile"
      }

      main "$@"
    '';
  };

  heyBotLog = pkgs.writeShellApplication {
    name = "hey-bot-log";
    text = ''
      TRANSCRIPTION_DIR="${cfg.transcriptionDir}"

      latestLogFile=$(find "$TRANSCRIPTION_DIR" -maxdepth 1 -name '*.log' -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)

      if [[ -z "''${latestLogFile:-}" ]]; then
        echo "No transcription logs found in $TRANSCRIPTION_DIR"
        exit 1
      fi

      if [[ "''${1:-}" == "-f" ]]; then
        tail -f "$latestLogFile"
      else
        cat "$latestLogFile"
      fi
    '';
  };

  heyBotPushToTalk = pkgs.writeShellApplication {
    name = "hey-bot-ptt";
    runtimeInputs = with pkgs; [
      python3Packages.edge-tts
      mpv
      curl
      jq
      libnotify
      pipewire
      wl-clipboard
    ];
    text = ''
      GATEWAY_URL="${cfg.gatewayUrl}"
      GATEWAY_TOKEN_FILE="${cfg.gatewayTokenFile}"
      AGENT_ID="${cfg.agentId}"
      TTS_VOICE="${cfg.ttsVoice}"
      MODEL="${cfg.model}"

      whisp-away stop --clipboard true 2>/dev/null

      TRANSCRIPTION="$(wl-paste 2>/dev/null || true)"

      if [[ -z "$TRANSCRIPTION" ]]; then
        notify-send "Hey Bot" "No speech detected" 2>/dev/null || true
        exit 0
      fi

      notify-send "Hey Bot" "$TRANSCRIPTION" 2>/dev/null || true

      GATEWAY_TOKEN=""
      if [[ -f "$GATEWAY_TOKEN_FILE" ]]; then
        GATEWAY_TOKEN=$(cat "$GATEWAY_TOKEN_FILE")
      fi

      RESPONSE_TEXT=$(curl -s --max-time 120 "$GATEWAY_URL/v1/chat/completions" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $GATEWAY_TOKEN" \
        -H "x-clawdbot-agent-id: $AGENT_ID" \
        -d "$(jq -n --arg text "$TRANSCRIPTION" --arg model "$MODEL" --arg agent "$AGENT_ID" '{
          model: $model,
          user: ("voice-" + $agent),
          messages: [{
            role: "user",
            content: ("[Voice input — respond concisely for TTS playback. Match spoken language (English or Portuguese).]\n\n" + $text)
          }]
        }')" | jq -r '.choices[0].message.content // "Sorry, I could not process that."')

      TTS_FILE=$(mktemp /tmp/hey-bot-ptt-XXXXXX.mp3)
      trap 'rm -f "$TTS_FILE"' EXIT

      if edge-tts --text "$RESPONSE_TEXT" --voice "$TTS_VOICE" --write-media "$TTS_FILE" 2>/dev/null; then
        wpctl set-mute @DEFAULT_AUDIO_SINK@ 0 2>/dev/null || true
        mpv --no-video --ao=pipewire "$TTS_FILE" 2>/dev/null || true
      fi
    '';
  };
in
{
  options.services.hey-bot = {
    enable = lib.mkEnableOption "Hey Bot always-on voice assistant";

    keywords = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      description = "Keywords to listen for (case-insensitive, used as grep -E alternation)";
    };

    gatewayUrl = lib.mkOption {
      type = lib.types.str;
      default = "http://localhost:18789";
    };

    gatewayTokenFile = lib.mkOption {
      type = lib.types.str;
      default = "/run/agenix/openclaw-gateway-token";
    };

    agentId = lib.mkOption {
      type = lib.types.str;
      default = "main";
    };

    ttsVoice = lib.mkOption {
      type = lib.types.str;
      default = "en-US-JennyNeural";
    };

    model = lib.mkOption {
      type = lib.types.str;
      default = "anthropic/claude-sonnet-4-5";
    };

    whisperModel = lib.mkOption {
      type = lib.types.str;
      default = "${config.home.homeDirectory}/.cache/whisper-cpp/models/ggml-base.bin";
    };

    transcriptionDir = lib.mkOption {
      type = lib.types.str;
      default = "${config.home.homeDirectory}/.local/share/hey-bot/transcriptions";
    };

    maxLogFileSize = lib.mkOption {
      type = lib.types.int;
      default = 1048576;
    };
  };

  config = lib.mkIf cfg.enable {
    home.packages = [
      heyBotDaemon
      heyBotPushToTalk
      heyBotLog
    ];

    systemd.user.services.hey-bot = {
      Unit = {
        Description = "Hey Bot - Always-on voice assistant";
        After = [ "pipewire.service" ];
      };
      Service = {
        Type = "simple";
        ExecStart = "${heyBotDaemon}/bin/hey-bot";
        Restart = "on-failure";
        RestartSec = 5;
      };
      Install = {
        WantedBy = [ "default.target" ];
      };
    };
  };
}
