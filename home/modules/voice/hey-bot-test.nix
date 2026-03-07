{
  config,
  lib,
  pkgs,
  ...
}:
let
  cfg = config.services.hey-bot;

  keywordsPrompt = builtins.concatStringsSep ", " cfg.keywords;

  heyBotTest = pkgs.writeShellApplication {
    name = "hey-bot-test";
    runtimeInputs = with pkgs; [
      whisper-cpp
      ffmpeg
      python3Packages.edge-tts
      sox
      jq
    ];
    text = ''
      readonly WHISPER_MODEL="${cfg.whisperModel}"
      readonly WHISPER_PROMPT="${keywordsPrompt}"
      readonly CACHE_DIR="$HOME/.cache/hey-bot-test"
      readonly CHUNK_DURATION=6
      readonly ENERGY_THRESHOLD=0.02

      main() {
        case "''${1:-}" in
          generate) _generate ;;
          sweep)
            if [[ -z "''${2:-}" ]]; then
              echo "Usage: hey-bot-test sweep <audio-file>"
              exit 1
            fi
            _sweep "$2"
            ;;
          run)
            if [[ -z "''${2:-}" ]]; then
              echo "Usage: hey-bot-test run <audio-file> [whisper-cli flags...]"
              exit 1
            fi
            shift
            _run "$@"
            ;;
          *)
            _usage
            ;;
        esac
      }

      _usage() {
        echo "Usage: hey-bot-test <command>"
        echo ""
        echo "Commands:"
        echo "  generate              Create synthetic test audio"
        echo "  sweep <audio-file>    Run parameter grid against audio"
        echo "  run <audio-file> [flags]  Single config test with custom whisper-cli flags"
        exit 1
      }

      _transcribe_with_config() {
        local chunkFile="$1"
        shift
        whisper-cli -m "$WHISPER_MODEL" -f "$chunkFile" -nt -np "$@" 2>/dev/null \
          | tr '\n' ' ' | sed 's/^ *//;s/ *$//;s/  */ /g' \
          | sed 's/\[BLANK_AUDIO\]//g; s/\[silence\]//gi; s/\[Music\]//gi; s/(humming)//gi; s/(singing)//gi' \
          | sed 's/^ *//;s/ *$//'
      }

      _split_into_chunks() {
        local audioFile="$1"
        local outputDir="$2"

        local duration
        duration=$(soxi -D "$audioFile")
        local chunkIndex=0
        local offset=0

        while awk "BEGIN {exit !($offset < $duration)}"; do
          sox "$audioFile" "$outputDir/chunk_$chunkIndex.wav" trim "$offset" "$CHUNK_DURATION" 2>/dev/null || break
          offset=$(awk "BEGIN {print $offset + $CHUNK_DURATION}")
          chunkIndex=$((chunkIndex + 1))
        done

        echo "$chunkIndex"
      }

      _generate() {
        mkdir -p "$CACHE_DIR"

        declare -a SENTENCES=(
          "en-US-JennyNeural|Hey clever, what is the weather like today?"
          "en-US-JennyNeural|Can you tell me about the latest news?"
          "pt-BR-FranciscaNeural|Ei clever, qual a previsao do tempo?"
          "pt-BR-FranciscaNeural|Me conta as ultimas noticias"
        )

        local segmentFiles=()
        local idx=0

        for entry in "''${SENTENCES[@]}"; do
          local voice="''${entry%%|*}"
          local text="''${entry#*|}"
          local segmentMp3="$CACHE_DIR/segment_$idx.mp3"
          local segmentWav="$CACHE_DIR/segment_$idx.wav"

          echo "Generating segment $((idx + 1)): $text"
          edge-tts --text "$text" --voice "$voice" --write-media "$segmentMp3"
          ffmpeg -y -i "$segmentMp3" -ar 16000 -ac 1 "$segmentWav" 2>/dev/null
          segmentFiles+=("$segmentWav")
          idx=$((idx + 1))
        done

        local silenceFile="$CACHE_DIR/silence.wav"
        sox -n -r 16000 -c 1 "$silenceFile" trim 0 3

        local concatArgs=()
        for i in "''${!segmentFiles[@]}"; do
          if [[ "$i" -gt 0 ]]; then
            concatArgs+=("$silenceFile")
          fi
          concatArgs+=("''${segmentFiles[$i]}")
        done

        local cleanFile="$CACHE_DIR/clean-audio.wav"
        sox "''${concatArgs[@]}" "$cleanFile"

        local duration
        duration=$(soxi -D "$cleanFile")
        local noiseFile="$CACHE_DIR/noise.wav"
        sox -n -r 16000 -c 1 "$noiseFile" synth "$duration" pinknoise vol 0.05

        local outputFile="$CACHE_DIR/test-audio.wav"
        sox -m "$cleanFile" "$noiseFile" "$outputFile"

        cat > "$CACHE_DIR/ground-truth.txt" << 'GROUNDTRUTH'
      Segment 1 (EN): Hey clever, what is the weather like today?
      Segment 2 (EN): Can you tell me about the latest news?
      Segment 3 (PT): Ei clever, qual a previsao do tempo?
      Segment 4 (PT): Me conta as ultimas noticias
      GROUNDTRUTH

        echo ""
        echo "Generated: $outputFile"
        echo "Ground truth: $CACHE_DIR/ground-truth.txt"
        echo "Duration: ''${duration}s"
      }

      _sweep() {
        local audioFile="$1"
        if [[ ! -f "$audioFile" ]]; then
          echo "File not found: $audioFile"
          exit 1
        fi

        chunkDir=$(mktemp -d /tmp/hey-bot-sweep-XXXXXX)
        trap 'rm -rf "$chunkDir"' EXIT

        local duration
        duration=$(soxi -D "$audioFile")
        local chunkCount
        chunkCount=$(_split_into_chunks "$audioFile" "$chunkDir")

        echo "Audio: $audioFile (''${duration}s, $chunkCount chunks of ''${CHUNK_DURATION}s)"
        echo ""

        for i in $(seq 0 $((chunkCount - 1))); do
          local chunkFile="$chunkDir/chunk_$i.wav"
          local startSec=$((i * CHUNK_DURATION))
          local endSec=$(( (i + 1) * CHUNK_DURATION ))
          local startTime
          startTime=$(printf "%d:%02d" $((startSec / 60)) $((startSec % 60)))
          local endTime
          endTime=$(printf "%d:%02d" $((endSec / 60)) $((endSec % 60)))

          local amplitude
          amplitude=$(sox "$chunkFile" -n stat 2>&1 | awk '/Maximum amplitude/ {print $3}')

          echo "Chunk $((i + 1)) ($startTime-$endTime) amplitude=$amplitude"

          local result

          result=$(_transcribe_with_config "$chunkFile" -l auto --suppress-nst)
          printf "  %-20s %s\n" "baseline:" "$result"

          result=$(_transcribe_with_config "$chunkFile" -l auto --suppress-nst --prompt "$WHISPER_PROMPT")
          printf "  %-20s %s\n" "with-prompt:" "$result"

          result=$(_transcribe_with_config "$chunkFile" -l auto --suppress-nst -bs 5 -bo 5)
          printf "  %-20s %s\n" "beam5:" "$result"

          result=$(_transcribe_with_config "$chunkFile" -l auto --suppress-nst -bs 5 -bo 5 --prompt "$WHISPER_PROMPT")
          printf "  %-20s %s\n" "beam5+prompt:" "$result"

          result=$(_transcribe_with_config "$chunkFile" -l auto --suppress-nst --entropy-thold 2.0 --no-speech-thold 0.8)
          printf "  %-20s %s\n" "conservative:" "$result"

          echo ""
        done
      }

      _run() {
        local audioFile="$1"
        shift
        local extraFlags=("$@")

        if [[ ! -f "$audioFile" ]]; then
          echo "File not found: $audioFile"
          exit 1
        fi

        chunkDir=$(mktemp -d /tmp/hey-bot-run-XXXXXX)
        trap 'rm -rf "$chunkDir"' EXIT

        local chunkCount
        chunkCount=$(_split_into_chunks "$audioFile" "$chunkDir")

        for i in $(seq 0 $((chunkCount - 1))); do
          local chunkFile="$chunkDir/chunk_$i.wav"

          local amplitude
          amplitude=$(sox "$chunkFile" -n stat 2>&1 | awk '/Maximum amplitude/ {print $3}')

          if [[ -z "$amplitude" ]] || awk "BEGIN {exit !($amplitude < $ENERGY_THRESHOLD)}"; then
            echo "Chunk $((i + 1)): [below energy threshold, amplitude=$amplitude]"
            continue
          fi

          local result
          result=$(_transcribe_with_config "$chunkFile" "''${extraFlags[@]}")
          echo "Chunk $((i + 1)) (amplitude=$amplitude): $result"
        done
      }

      main "$@"
    '';
  };
in
{
  config = lib.mkIf cfg.enable {
    home.packages = [ heyBotTest ];
  };
}
