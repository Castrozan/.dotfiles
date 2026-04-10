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

  find = "${pkgs.findutils}/bin/find";
  mktemp = "${pkgs.coreutils}/bin/mktemp";
  mkdir = "${pkgs.coreutils}/bin/mkdir";
  ln = "${pkgs.coreutils}/bin/ln";
  dirname = "${pkgs.coreutils}/bin/dirname";
  basename = "${pkgs.coreutils}/bin/basename";
  realpath = "${pkgs.coreutils}/bin/realpath";
  rm = "${pkgs.coreutils}/bin/rm";

  claudeConfigDir = "${homeDirectory}/.claude";

  claudeWorkspaceScript = pkgs.writeScriptBin "claude-workspace" ''
    #!${pkgs.fish}/bin/fish

    set -l extend false
    set -l from_dirs
    set -l remaining_args
    set -l skip_next false

    for i in (seq (count $argv))
      if test "$skip_next" = true
        set skip_next false
        continue
      end
      switch $argv[$i]
        case --extend
          set extend true
        case --from
          set -l next (math $i + 1)
          if test $next -le (count $argv)
            set -a from_dirs $argv[$next]
            set skip_next true
          else
            echo "error: --from requires a directory argument"
            exit 1
          end
        case '*'
          set -a remaining_args $argv[$i]
      end
    end

    # Create isolated config dir that mirrors ~/.claude but replaces skills/
    set -l tmpdir (${mktemp} -d -t claude-workspace.XXXXXX)
    set -l config_dir "$tmpdir/claude-config"
    ${mkdir} -p "$config_dir/skills"

    # Symlink everything from ~/.claude except skills/
    for item in ${claudeConfigDir}/* ${claudeConfigDir}/.*
      set -l name (${basename} "$item")
      if test "$name" = "." -o "$name" = ".."
        continue
      end
      if test "$name" = "skills"
        continue
      end
      ${ln} -sfn "$item" "$config_dir/$name"
    end

    # Ensure .claude.json exists so Claude can write its runtime state
    if not test -e "$config_dir/.claude.json"
      echo '{}' > "$config_dir/.claude.json"
    end

    set -l skill_count 0

    if test (count $from_dirs) -gt 0
      # --from mode: load each directory as a whole skill (by its root SKILL.md)
      for dir in $from_dirs
        if test -z "$dir" -o ! -d "$dir"
          echo "error: '$dir' is not a valid directory"
          ${rm} -rf "$tmpdir"
          exit 1
        end
        set -l abs_dir (${realpath} "$dir")
        if not test -f "$abs_dir/SKILL.md"
          echo "error: no SKILL.md found at root of $dir"
          ${rm} -rf "$tmpdir"
          exit 1
        end
        set -l skill_name (${basename} "$abs_dir")
        ${ln} -sfn "$abs_dir" "$config_dir/skills/$skill_name"
        set skill_count (math $skill_count + 1)
      end
    else
      # Default mode: scan cwd for SKILL.md files
      set -l skill_files (${find} . -name "SKILL.md" -type f 2>/dev/null)

      if test (count $skill_files) -gt 0
        for skill_file in $skill_files
          set -l skill_dir (${dirname} "$skill_file")
          set -l abs_skill_dir (${realpath} "$skill_dir")
          set -l skill_name (${basename} "$abs_skill_dir")
          ${ln} -sfn "$abs_skill_dir" "$config_dir/skills/$skill_name"
          set skill_count (math $skill_count + 1)
        end
      end
    end

    # Error if no skills at all (no --from, no SKILL.md, no --extend)
    if test "$skill_count" -eq 0 -a "$extend" = false
      echo "No skills to load. Use --from <dir>, run from a dir with SKILL.md files, or use --extend."
      ${rm} -rf "$tmpdir"
      exit 1
    end

    # With --extend, merge base and personal skills
    set -l cmd_args
    if test "$extend" = true
      for skill in ${claudeConfigDir}/skills/*/
        set -l skill_name (${basename} "$skill")
        if not test -e "$config_dir/skills/$skill_name"
          ${ln} -sfn "$skill" "$config_dir/skills/$skill_name"
        end
      end
      set -a cmd_args --add-dir ${personalSkillSetDirectory}
    end

    echo "Loaded workspace:"
    for skill in $config_dir/skills/*/
      echo "  - "(${basename} "$skill")
    end

    CLAUDE_CONFIG_DIR="$config_dir" command claude $cmd_args $remaining_args
    set -l exit_code $status

    ${rm} -rf "$tmpdir"
    exit $exit_code
  '';
in
{
  home.packages = [ claudeWorkspaceScript ];

  xdg.configFile."fish/conf.d/claude-skill-sets.fish".text = defaultClaudeFishFunction;
}
