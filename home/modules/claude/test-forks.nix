{
  config,
  pkgs,
  lib,
  ...
}:
let
  homeDir = config.home.homeDirectory;
  testForksBase = "${homeDir}/.claude/test-forks";
  personalSkillSetDirectory = "${homeDir}/.local/share/claude-skill-sets/personal";
  bunBin = "${homeDir}/.bun/bin";

  # mcx is installed via `bun add -g` (lives in ~/.bun/bin/mcx).
  # The wrapper ensures bun is in PATH for mcx's #!/usr/bin/env bun shebang.
  mcxServeWrapper = pkgs.writeShellScript "mcx-serve" ''
    export PATH="${bunBin}:$PATH"
    exec ${bunBin}/mcx serve "$@"
  '';

  # MCX hook scripts — deny native tools, redirect to mcx equivalents.
  # Source: https://github.com/schizoidcock/mcx/tree/main/hooks
  mcxHookRedirect = pkgs.writeText "mcx-redirect.js" ''
    const input = await Bun.stdin.json();
    const mcx = { Grep: "mcx_grep", Glob: "mcx_find", Edit: "mcx_edit", Write: "mcx_write" }[input.tool_name];
    if (mcx) {
      console.log(JSON.stringify({
        hookSpecificOutput: {
          hookEventName: "PreToolUse",
          permissionDecision: "deny",
          additionalContext: `Use ${"$"}{mcx} instead`
        }
      }));
    }
  '';

  mcxHookReadCheck = pkgs.writeText "mcx-read-check.js" ''
    const input = await Bun.stdin.json();
    const filePath = input.tool_input?.file_path;
    if (filePath) {
      try {
        const size = Bun.file(filePath).size;
        if (size > 50 * 1024) {
          const sizeKB = Math.round(size / 1024);
          console.log(JSON.stringify({
            hookSpecificOutput: {
              hookEventName: "PreToolUse",
              permissionDecision: "deny",
              additionalContext: `File is ${"$"}{sizeKB}KB. Use mcx_file({ path: "${"$"}{filePath}", storeAs: "src" }) + grep/around/outline to explore. Use mcx_edit to modify.`
            }
          }));
        }
      } catch {}
    }
  '';

  mcxHookBashCheck = pkgs.writeText "mcx-bash-check.js" ''
    const input = await Bun.stdin.json();
    const command = input.tool_input?.command || "";
    const cmd = command.trim();
    if (/^cat\s+/.test(cmd)) {
      console.log(JSON.stringify({ hookSpecificOutput: { hookEventName: "PreToolUse", permissionDecision: "deny", additionalContext: "Use mcx_file({ path, storeAs }) instead of cat" } }));
    } else if (/^grep\s+/.test(cmd) || /^rg\s+/.test(cmd)) {
      console.log(JSON.stringify({ hookSpecificOutput: { hookEventName: "PreToolUse", permissionDecision: "deny", additionalContext: "Use mcx_grep instead of grep/rg" } }));
    } else if (/^find\s+/.test(cmd) || /^ls\s+.*\*/.test(cmd)) {
      console.log(JSON.stringify({ hookSpecificOutput: { hookEventName: "PreToolUse", permissionDecision: "deny", additionalContext: "Use mcx_find instead of find/ls" } }));
    } else if (/<<\s*['"]?EOF/.test(cmd) || /^echo\s+.*>/.test(cmd)) {
      console.log(JSON.stringify({ hookSpecificOutput: { hookEventName: "PreToolUse", permissionDecision: "deny", additionalContext: "Use mcx_edit or mcx_write instead of heredoc/echo redirection" } }));
    }
  '';

  mcxHooksDir = "${testForksBase}/mcx/.claude/hooks";

  mcxProjectSettings = builtins.toJSON {
    hooks = {
      PreToolUse = [
        {
          matcher = "Grep";
          hooks = [
            {
              type = "command";
              command = "${bunBin}/bun ${mcxHooksDir}/mcx-redirect.js";
            }
          ];
        }
        {
          matcher = "Glob";
          hooks = [
            {
              type = "command";
              command = "${bunBin}/bun ${mcxHooksDir}/mcx-redirect.js";
            }
          ];
        }
        {
          matcher = "Edit";
          hooks = [
            {
              type = "command";
              command = "${bunBin}/bun ${mcxHooksDir}/mcx-redirect.js";
            }
          ];
        }
        {
          matcher = "Write";
          hooks = [
            {
              type = "command";
              command = "${bunBin}/bun ${mcxHooksDir}/mcx-redirect.js";
            }
          ];
        }
        {
          matcher = "Read";
          hooks = [
            {
              type = "command";
              command = "${bunBin}/bun ${mcxHooksDir}/mcx-read-check.js";
            }
          ];
        }
        {
          matcher = "Bash";
          hooks = [
            {
              type = "command";
              command = "${bunBin}/bun ${mcxHooksDir}/mcx-bash-check.js";
            }
          ];
        }
      ];
    };
  };

  mcxClaudeMd = ''
    # MCX Test Fork

    You MUST use MCX tools instead of native Claude Code tools. This is the entire point of this environment.

    ## Tool mapping (always use the mcx version)
    | Instead of | Use |
    |-----------|-----|
    | Read | mcx_file (stores in sandbox, use outline/grep/around to query) |
    | Grep | mcx_grep (SIMD-accelerated, fuzzy) |
    | Glob | mcx_find (frecency + proximity ranking) |
    | Edit | mcx_edit (no read-first requirement) |
    | Write | mcx_write (no read-first requirement) |
    | Bash cat/grep/find | mcx_file / mcx_grep / mcx_find |

    ## Workflow
    1. Use `mcx_find` to locate files (not Glob)
    2. Use `mcx_file({ path, storeAs: "name" })` to load files into sandbox (not Read)
    3. Use `outline($name)` to see structure, `grep($name, "pattern")` to search, `around($name, line, ctx)` for context
    4. Use `mcx_grep` for cross-file search (not Grep)
    5. Use `mcx_edit` to modify files (not Edit)
    6. Use `mcx_execute` for data processing — filter/transform data inside the sandbox, return only results

    ## Key helpers in sandbox
    ```
    pick(data, ['field1', 'field2'])  — extract fields
    first(data, N)                    — first N items
    sum(data, 'field')                — sum numeric field
    count(data, 'field')              — count by field
    table(data, N)                    — markdown table
    outline($file)                    — function/class signatures
    around($file, line, ctx)          — lines around a position
    grep($file, pattern, ctx)         — search within stored file
    lines($file, from, to)            — get line range
    block($file, line)                — extract code block
    ```

    ## Variable persistence
    Results auto-store as `$result`. Use custom names with `storeAs`. Variables survive across calls.
    Stale variables (>5min, >1KB) auto-compress.
  '';

  testForks = {
    mcx = {
      description = "MCX (Modular Code Execution) sandbox";
      mcpServers = {
        mcx = {
          command = "${mcxServeWrapper}";
          args = [ ];
        };
      };
      claudeMd = mcxClaudeMd;
      projectSettings = mcxProjectSettings;
      hookFiles = {
        "mcx-redirect.js" = mcxHookRedirect;
        "mcx-read-check.js" = mcxHookReadCheck;
        "mcx-bash-check.js" = mcxHookBashCheck;
      };
      extraPackages = [ ];
    };
  };

  generateFishFunction =
    name: fork:
    let
      workspaceDir = "${testForksBase}/${name}";
    in
    ''
      function claude-${name} --description "${fork.description}"
        cd ${workspaceDir} && command claude --add-dir ${personalSkillSetDirectory} $argv
      end
    '';

  allFishFunctions = lib.concatStringsSep "\n" (lib.mapAttrsToList generateFishFunction testForks);

  generateWorkspaceActivation =
    name: fork:
    let
      workspaceDir = "${testForksBase}/${name}";
      mcpJsonFile = pkgs.writeText "test-fork-${name}-mcp.json" (
        builtins.toJSON { mcpServers = fork.mcpServers; }
      );
      claudeMdFile = pkgs.writeText "test-fork-${name}-claude.md" fork.claudeMd;
      projectSettingsFile = pkgs.writeText "test-fork-${name}-settings.json" (
        fork.projectSettings or "{}"
      );
      hookFilesDeployment = lib.concatStringsSep "\n" (
        lib.mapAttrsToList (hookName: hookSrc: ''
          cp --no-preserve=mode ${hookSrc} "${workspaceDir}/.claude/hooks/${hookName}"
        '') (fork.hookFiles or { })
      );
    in
    ''
      mkdir -p "${workspaceDir}/.claude/hooks"
      cp --no-preserve=mode ${mcpJsonFile} "${workspaceDir}/.mcp.json"
      cp --no-preserve=mode ${claudeMdFile} "${workspaceDir}/CLAUDE.md"
      cp --no-preserve=mode ${projectSettingsFile} "${workspaceDir}/.claude/settings.json"
      ${hookFilesDeployment}
    '';

  allWorkspaceActivations = lib.concatStringsSep "\n" (
    lib.mapAttrsToList generateWorkspaceActivation testForks
  );

  allExtraPackages = lib.concatMap (fork: fork.extraPackages or [ ]) (lib.attrValues testForks);
in
{
  xdg.configFile."fish/conf.d/claude-test-forks.fish".text = allFishFunctions;

  home = {
    packages = allExtraPackages;

    activation.createTestForkWorkspaces = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      ${allWorkspaceActivations}
    '';
  };
}
