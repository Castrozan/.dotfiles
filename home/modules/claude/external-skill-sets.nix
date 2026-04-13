{
  config,
  lib,
  pkgs,
  ...
}:
let
  inherit (config.home) homeDirectory;
  skillSetsBaseDirectory = "${homeDirectory}/.local/share/claude-skill-sets";
  personalSkillSetDirectory = "${skillSetsBaseDirectory}/personal";

  defaultClaudeFishFunction = ''
    function claude --description "Claude Code with personal skills"
      command claude --add-dir ${personalSkillSetDirectory} $argv
    end
  '';

  claudeConfigDir = "${homeDirectory}/.claude";

  claudeWorkspaceScript = pkgs.writeShellScriptBin "claude-workspace" ''
    export PATH="${
      lib.makeBinPath (
        with pkgs;
        [
          coreutils
          findutils
        ]
      )
    }:$PATH"

    extend=false
    from_dirs=()
    remaining_args=()

    while [[ $# -gt 0 ]]; do
      case "$1" in
        --extend)
          extend=true
          shift
          ;;
        --from)
          if [[ -z "''${2:-}" ]]; then
            echo "error: --from requires a directory argument"
            exit 1
          fi
          from_dirs+=("$2")
          shift 2
          ;;
        --)
          shift
          remaining_args+=("$@")
          break
          ;;
        *)
          remaining_args+=("$1")
          shift
          ;;
      esac
    done

    cleanup() { rm -rf "$tmpdir"; }
    trap cleanup EXIT

    tmpdir=$(mktemp -d -t claude-workspace.XXXXXX)
    config_dir="$tmpdir/claude-config"
    mkdir -p "$config_dir/skills"

    # Symlink everything from ~/.claude except skills/
    for item in ${claudeConfigDir}/* ${claudeConfigDir}/.*; do
      name=$(basename "$item")
      [[ "$name" == "." || "$name" == ".." || "$name" == "skills" ]] && continue
      ln -sfn "$item" "$config_dir/$name"
    done

    # Symlink global ~/.claude.json for onboarding state and runtime config
    if [[ -e "${homeDirectory}/.claude.json" && ! -e "$config_dir/.claude.json" ]]; then
      ln -sfn "${homeDirectory}/.claude.json" "$config_dir/.claude.json"
    elif [[ ! -e "$config_dir/.claude.json" ]]; then
      echo '{}' > "$config_dir/.claude.json"
    fi

    skill_count=0

    if [[ ''${#from_dirs[@]} -gt 0 ]]; then
      for dir in "''${from_dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
          echo "error: '$dir' is not a valid directory"
          exit 1
        fi
        abs_dir=$(realpath "$dir")
        if [[ ! -f "$abs_dir/SKILL.md" ]]; then
          echo "error: no SKILL.md found at root of $dir"
          exit 1
        fi
        skill_name=$(basename "$abs_dir")
        ln -sfn "$abs_dir" "$config_dir/skills/$skill_name"
        ((skill_count++))
      done
    else
      while IFS= read -r skill_file; do
        skill_dir=$(dirname "$skill_file")
        abs_skill_dir=$(realpath "$skill_dir")
        skill_name=$(basename "$abs_skill_dir")
        ln -sfn "$abs_skill_dir" "$config_dir/skills/$skill_name"
        ((skill_count++))
      done < <(find . -name "SKILL.md" -type f 2>/dev/null)
    fi

    if [[ "$skill_count" -eq 0 && "$extend" == false ]]; then
      echo "No skills to load. Use --from <dir>, run from a dir with SKILL.md files, or use --extend."
      exit 1
    fi

    cmd_args=()
    if [[ "$extend" == true ]]; then
      for skill in ${claudeConfigDir}/skills/*/; do
        [[ -d "$skill" ]] || continue
        skill_name=$(basename "$skill")
        [[ -e "$config_dir/skills/$skill_name" ]] || ln -sfn "$skill" "$config_dir/skills/$skill_name"
      done
      cmd_args+=(--add-dir "${personalSkillSetDirectory}")
    fi

    echo "Loaded workspace:"
    for skill in "$config_dir/skills"/*/; do
      [[ -d "$skill" ]] || continue
      echo "  - $(basename "$skill")"
    done

    CLAUDE_CONFIG_DIR="$config_dir" exec claude "''${cmd_args[@]}" "''${remaining_args[@]}"
  '';
in
{
  home.packages = [ claudeWorkspaceScript ];

  xdg.configFile."fish/conf.d/claude-skill-sets.fish".text = defaultClaudeFishFunction;
}
