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
      perl
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
      readonly COMMAND_MAX_CHUNKS=15
      readonly COMMAND_SILENCE_END=3
      readonly FOLLOWUP_WINDOW_CHUNKS=5
      readonly ENERGY_THRESHOLD=0.02

      COMMAND_MODE=false
      COMMAND_BUFFER=""
      KEYWORD_PHRASE=""
      COMMAND_SILENT_COUNT=0
      COMMAND_CHUNK_COUNT=0
      FOLLOWUP_ACTIVE=false
      FOLLOWUP_CHUNKS_REMAINING=0
      FOLLOWUP_FLAG_FILE="/tmp/hey-bot-followup-$$"
      WAIT_CONTEXT_FILE="/tmp/hey-bot-wait-context-$$"
      PREV_CHUNK=""
      PREV_REC_PID=""
      GATEWAY_TOKEN=""

      main() {
        mkdir -p "$TRANSCRIPTION_DIR"
        _load_gateway_token
        trap '_cleanup' EXIT
        echo "hey-bot: listening for keywords matching: $KEYWORDS_PATTERN"
        _recording_loop
      }

      _load_gateway_token() {
        if [[ -f "$GATEWAY_TOKEN_FILE" ]]; then
          GATEWAY_TOKEN=$(cat "$GATEWAY_TOKEN_FILE")
        fi
      }

      _cleanup() {
        jobs -p 2>/dev/null | xargs -r kill 2>/dev/null || true
        rm -f "$FOLLOWUP_FLAG_FILE" "$WAIT_CONTEXT_FILE"
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
        local transcription=""

        if _chunk_has_audio "$chunkFile"; then
          transcription=$(_transcribe_chunk "$chunkFile")
        fi
        rm -f "$chunkFile"

        local wordCount=0
        if [[ -n "$transcription" ]]; then
          wordCount=$(echo "$transcription" | wc -w)
          if [[ "$wordCount" -ge 3 ]]; then
            _log_transcription "$transcription"
          fi
        fi

        _check_followup_signal

        if [[ "$COMMAND_MODE" == "true" ]]; then
          _handle_command_chunk "$transcription"
          return
        fi

        if [[ "$FOLLOWUP_ACTIVE" == "true" ]]; then
          _handle_followup_chunk "$transcription" "$wordCount"
          return
        fi

        if [[ -f /tmp/hey-bot-keywords-disabled ]]; then
          return
        fi

        if [[ -n "$transcription" ]] && echo "$transcription" | grep -qiE "$KEYWORDS_PATTERN"; then
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
        local rawTranscription
        rawTranscription=$(whisper-cli -m "$WHISPER_MODEL" -f "$chunkFile" -nt -np -l auto --suppress-nst 2>/dev/null \
          | tr '\n' ' ' | sed 's/^ *//;s/ *$//;s/  */ /g' \
          | sed 's/\[BLANK_AUDIO\]//g; s/\[silence\]//gi; s/\[Music\]//gi; s/(humming)//gi; s/(singing)//gi' \
          | sed 's/^ *//;s/ *$//')

        if _is_non_latin_hallucination "$rawTranscription"; then
          echo ""
        else
          echo "$rawTranscription"
        fi
      }

      _is_non_latin_hallucination() {
        local text="$1"
        [[ -z "$text" ]] && return 1
        echo "$text" | perl -CSD -e '
          use utf8;
          my $line = <STDIN>;
          chomp $line;
          my $total = length($line);
          exit 1 if $total == 0;
          my $nonLatin = () = $line =~ /[^\p{Latin}\p{Common}\p{Inherited}]/g;
          exit($nonLatin > $total * 0.3 ? 0 : 1);
        '
      }

      _check_followup_signal() {
        if [[ -f "$FOLLOWUP_FLAG_FILE" ]]; then
          rm -f "$FOLLOWUP_FLAG_FILE"
          if [[ "$COMMAND_MODE" != "true" ]]; then
            FOLLOWUP_ACTIVE=true
            FOLLOWUP_CHUNKS_REMAINING=$FOLLOWUP_WINDOW_CHUNKS
            echo "hey-bot: follow-up window active"
          fi
        fi
      }

      _handle_command_chunk() {
        local transcription="$1"

        COMMAND_CHUNK_COUNT=$((COMMAND_CHUNK_COUNT + 1))

        if [[ -n "$transcription" ]]; then
          COMMAND_BUFFER="$COMMAND_BUFFER $transcription"
          COMMAND_SILENT_COUNT=0
        else
          COMMAND_SILENT_COUNT=$((COMMAND_SILENT_COUNT + 1))
        fi

        if [[ "$COMMAND_SILENT_COUNT" -ge "$COMMAND_SILENCE_END" ]] || [[ "$COMMAND_CHUNK_COUNT" -ge "$COMMAND_MAX_CHUNKS" ]]; then
          _dispatch_command
        fi
      }

      _handle_followup_chunk() {
        local transcription="$1"
        local wordCount="$2"

        FOLLOWUP_CHUNKS_REMAINING=$((FOLLOWUP_CHUNKS_REMAINING - 1))

        if [[ -n "$transcription" ]] && [[ "$wordCount" -ge 4 ]]; then
          echo "hey-bot: follow-up detected"
          FOLLOWUP_ACTIVE=false
          FOLLOWUP_CHUNKS_REMAINING=0
          _activate_command_mode "$transcription" "$wordCount"
          return
        fi

        if [[ "$FOLLOWUP_CHUNKS_REMAINING" -le 0 ]]; then
          FOLLOWUP_ACTIVE=false
          echo "hey-bot: follow-up window expired"
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
        COMMAND_BUFFER=""
        COMMAND_SILENT_COUNT=0
        COMMAND_CHUNK_COUNT=0

        if [[ -f "$WAIT_CONTEXT_FILE" ]]; then
          local waitContext
          waitContext=$(cat "$WAIT_CONTEXT_FILE")
          rm -f "$WAIT_CONTEXT_FILE"
          KEYWORD_PHRASE="$waitContext $transcription"
          echo "hey-bot: prepending wait context: '$waitContext'"
        else
          KEYWORD_PHRASE="$transcription"
        fi
      }

      _dispatch_command() {
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
        COMMAND_SILENT_COUNT=0
        COMMAND_CHUNK_COUNT=0
      }

      _process_command() {
        set +e
        _process_command_inner "$@"
        local exitCode=$?
        set -e
        if [[ "$exitCode" -ne 0 ]]; then
          echo "hey-bot: background command failed with exit code $exitCode"
        fi
      }

      _process_command_inner() {
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

        if [[ "$responseText" == "WAIT" ]]; then
          echo "hey-bot: mid-sentence detected, waiting for continuation"
          echo "$commandText" > "$WAIT_CONTEXT_FILE"
          touch "$FOLLOWUP_FLAG_FILE"
          return
        fi

        _speak_response "$responseText"
        touch "$FOLLOWUP_FLAG_FILE"
      }

      _send_to_gateway() {
        local commandText="$1"
        local recentTranscription
        recentTranscription=$(tail -20 "$(_get_log_file)" 2>/dev/null || echo "")

        local rawResponse
        rawResponse=$(curl -s --max-time 120 "$GATEWAY_URL/v1/chat/completions" \
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
                content: ("[Voice input from microphone transcription. Rules: (1) Respond concisely for TTS playback, max 3 sentences. (2) Match spoken language (English or Portuguese). (3) Never include file paths, code blocks, URLs, or technical formatting. (4) If the transcription is nonsensical, garbled, or clearly not directed at you, respond with exactly IGNORE and nothing else. (5) If the transcription appears cut mid-sentence or the user seems to still be speaking, respond with exactly WAIT and nothing else. (6) If the transcription appears to be your OWN previous TTS response being re-transcribed by the microphone (sounds like something an AI assistant would say rather than a human), respond with exactly IGNORE and nothing else — this prevents feedback loops when using speakers.]\n\n[Recent ambient transcription for context:]\n" + $context + "\n\n[Command:]\n" + $text)
              }]
            }')" || true)

        if [[ -z "$rawResponse" ]]; then
          echo "Sorry, I could not reach the gateway."
          return
        fi

        local parsedContent
        parsedContent=$(echo "$rawResponse" | jq -r '.choices[0].message.content // empty' 2>/dev/null || true)

        if [[ -n "$parsedContent" ]]; then
          echo "$parsedContent"
        else
          echo "hey-bot: gateway raw response: $(echo "$rawResponse" | head -c 300)" >&2
          echo "Sorry, I could not process that."
        fi
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
