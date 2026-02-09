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
      WHISPER_MODEL="${cfg.whisperModel}"
      KEYWORDS_PATTERN="${keywordsPattern}"
      GATEWAY_URL="${cfg.gatewayUrl}"
      GATEWAY_TOKEN_FILE="${cfg.gatewayTokenFile}"
      AGENT_ID="${cfg.agentId}"
      TTS_VOICE="${cfg.ttsVoice}"
      MODEL="${cfg.model}"
      TRANSCRIPTION_DIR="${cfg.transcriptionDir}"
      MAX_LOG_SIZE=${toString cfg.maxLogFileSize}

      mkdir -p "$TRANSCRIPTION_DIR"

      get_log_file() {
        local currentLogFile="$TRANSCRIPTION_DIR/current.log"
        if [[ -f "$currentLogFile" ]] && [[ $(stat -c%s "$currentLogFile") -gt $MAX_LOG_SIZE ]]; then
          mv "$currentLogFile" "$TRANSCRIPTION_DIR/$(date +%Y-%m-%d_%H-%M-%S).log"
        fi
        echo "$currentLogFile"
      }

      log_transcription() {
        local transcriptionText="$1"
        local logFile
        logFile=$(get_log_file)
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] $transcriptionText" >> "$logFile"
      }

      GATEWAY_TOKEN=""
      if [[ -f "$GATEWAY_TOKEN_FILE" ]]; then
        GATEWAY_TOKEN=$(cat "$GATEWAY_TOKEN_FILE")
      fi

      echo "hey-bot: listening for keywords matching: $KEYWORDS_PATTERN"

      while true; do
        CHUNK_FILE=$(mktemp /tmp/hey-bot-XXXXXX.wav)

        rec -q "$CHUNK_FILE" rate 16k channels 1 trim 0 8 2>/dev/null || { rm -f "$CHUNK_FILE"; continue; }

        MAX_AMPLITUDE=$(sox "$CHUNK_FILE" -n stat 2>&1 | awk '/Maximum amplitude/ {print $3}')
        if [[ -z "$MAX_AMPLITUDE" ]] || awk "BEGIN {exit !($MAX_AMPLITUDE < 0.02)}"; then
          rm -f "$CHUNK_FILE"
          continue
        fi

        TRANSCRIBED_TEXT=$(whisper-cli -m "$WHISPER_MODEL" -f "$CHUNK_FILE" -nt -np -l auto --suppress-nst \
          2>/dev/null \
          | tr '\n' ' ' | sed 's/^ *//;s/ *$//;s/  */ /g' \
          | sed 's/\[BLANK_AUDIO\]//g; s/\[silence\]//gi; s/\[Music\]//gi; s/(humming)//gi; s/(singing)//gi' \
          | sed 's/^ *//;s/ *$//')
        rm -f "$CHUNK_FILE"

        if [[ -z "$TRANSCRIBED_TEXT" ]]; then
          continue
        fi

        log_transcription "$TRANSCRIBED_TEXT"

        if ! echo "$TRANSCRIBED_TEXT" | grep -qiE "$KEYWORDS_PATTERN"; then
          continue
        fi

        echo "hey-bot: keyword detected in: '$TRANSCRIBED_TEXT'"
        notify-send "Hey Bot" "Listening..." 2>/dev/null || true

        COMMAND_FILE=$(mktemp /tmp/hey-bot-cmd-XXXXXX.wav)
        rec -q "$COMMAND_FILE" rate 16k channels 1 \
          silence 1 0.2 2% 1 2.0 2% trim 0 30 2>/dev/null || { rm -f "$COMMAND_FILE"; continue; }

        COMMAND_TEXT=$(whisper-cli -m "$WHISPER_MODEL" -f "$COMMAND_FILE" -nt -np -l en 2>/dev/null \
          | tr '\n' ' ' | sed 's/^ *//;s/ *$//;s/  */ /g' | sed 's/\[BLANK_AUDIO\]//g' | sed 's/^ *//;s/ *$//')
        rm -f "$COMMAND_FILE"

        if [[ -z "$COMMAND_TEXT" ]]; then
          echo "hey-bot: empty command, returning to listening"
          continue
        fi

        echo "hey-bot: command: '$COMMAND_TEXT'"
        log_transcription "[COMMAND] $COMMAND_TEXT"
        notify-send "Hey Bot" "$COMMAND_TEXT" 2>/dev/null || true

        LOG_FILE=$(get_log_file)

        RESPONSE_TEXT=$(curl -s --max-time 120 "$GATEWAY_URL/v1/chat/completions" \
          -H "Content-Type: application/json" \
          -H "Authorization: Bearer $GATEWAY_TOKEN" \
          -H "x-clawdbot-agent-id: $AGENT_ID" \
          -d "$(jq -n \
            --arg text "$COMMAND_TEXT" \
            --arg model "$MODEL" \
            --arg agent "$AGENT_ID" \
            --arg logfile "$LOG_FILE" \
            '{
              model: $model,
              user: ("voice-" + $agent),
              messages: [{
                role: "user",
                content: ("[Voice input — respond concisely for TTS playback. Match spoken language (English or Portuguese). Ambient transcription log: " + $logfile + "]\n\n" + $text)
              }]
            }')" | jq -r '.choices[0].message.content // "Sorry, I could not process that."')

        echo "hey-bot: response: '$(echo "$RESPONSE_TEXT" | head -c 200)'"
        log_transcription "[RESPONSE] $RESPONSE_TEXT"

        TTS_FILE=$(mktemp /tmp/hey-bot-tts-XXXXXX.mp3)
        if edge-tts --text "$RESPONSE_TEXT" --voice "$TTS_VOICE" --write-media "$TTS_FILE" 2>/dev/null; then
          wpctl set-mute @DEFAULT_AUDIO_SINK@ 0 2>/dev/null || true
          mpv --no-video --ao=pipewire "$TTS_FILE" 2>/dev/null || true
        fi
        rm -f "$TTS_FILE"

        echo "hey-bot: ready for next keyword"
      done
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
