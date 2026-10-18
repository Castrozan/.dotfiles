{
  pkgs,
  lib,
  hostname,
  homeDirectory,
  chromePackage,
  isDarwin ? pkgs.stdenv.isDarwin,
}:
let
  wellputSource = import ../wellput-plugin/upstream.nix { inherit pkgs; };
  projection = import ../instruction-projection.nix { inherit pkgs; };
  browser = import ../skills/workstation/browser/install {
    inherit pkgs chromePackage;
    homeDir = homeDirectory;
    nodejs = pkgs.nodejs_22;
  };
  skillCatalog = import ../interactive-skill-catalog/interactive-agent-skills.nix {
    inherit pkgs hostname;
  };
  interactiveSkillNames = skillCatalog.effectiveInteractiveSkillNames { };
  skillPath =
    name:
    if builtins.elem name interactiveSkillNames then "skills/${name}" else "library/skills/${name}";
  destinations =
    builtins.listToAttrs (
      map (name: {
        name = builtins.unsafeDiscardStringContext (
          toString skillCatalog.skillSourceDirectoryByName.${name}
        );
        value = "/plugin/${skillPath name}";
      }) skillCatalog.allSkillNames
    )
    // {
      "${toString ../core-rules/core.md}" = "/plugin/skills/core/SKILL.md";
      "${toString ../interactive-communication.md}" = "/plugin/instructions/interactive.md";
    };
  skillEntries = map (
    name:
    let
      skillDirectory = projection.skillDirectory {
        source = skillCatalog.skillSourceDirectoryByName.${name};
        deployed = "/plugin/${skillPath name}";
        inherit destinations;
      };
    in
    {
      name = skillPath name;
      path =
        if name == "research" then
          import ../skills/knowledge/research/pulse/install.nix { inherit pkgs skillDirectory; }
        else
          skillDirectory;
    }
  ) skillCatalog.allSkillNames;
  generatedSkill = name: description: body: {
    name = "skills/${name}/SKILL.md";
    path = projection.instructionText {
      name = "dotfiles-${name}-SKILL.md";
      deployed = "/plugin/skills/${name}/SKILL.md";
      inherit destinations;
      text = ''
        ---
        name: ${name}
        description: ${builtins.toJSON description}
        ---

        ${body}
      '';
    };
  };
  allSkillsIndex = skillCatalog.renderAllSkillsIndexSkill interactiveSkillNames;
  artifactEntries =
    skillEntries
    ++ [
      (generatedSkill "core" "Display the canonical core agent instructions." (
        builtins.readFile ../core-rules/core.md
      ))
      (generatedSkill "all-skills" allSkillsIndex.description allSkillsIndex.body)
      {
        name = "instructions/core.md";
        path = ../core-rules/core.md;
      }
      {
        name = "instructions/interactive.md";
        path = projection.instructionFile {
          name = "dotfiles-interactive-instructions.md";
          sources = [ ../interactive-communication.md ];
          deployed = "/plugin/instructions/interactive.md";
          inherit destinations;
        };
      }
      {
        name = "native/wellput";
        path = wellputSource;
      }
      {
        name = "hooks";
        path = import ../../hooks/flat-hook-scripts-directory.nix { inherit pkgs lib; };
      }
      {
        name = "native/browser/chrome-devtools";
        path = "${browser.chromeDevtoolsCli}/bin/chrome-devtools";
      }
      {
        name = "native/hermes/hook-bridge";
        path =
          (import ../../hooks/integrations/hermes/hermes-hooks.nix {
            inherit
              pkgs
              lib
              hostname
              isDarwin
              ;
          }).hermesHookCommand;
      }
      {
        name = "native/hermes/translate_hermes_hook_call.py";
        path = ../../hooks/integrations/hermes/translate_hermes_hook_call.py;
      }
      {
        name = "native/pi/human-facing-reply-guard.js";
        path = import ../../harnesses/pi/extensions { inherit pkgs lib; };
      }
      {
        name = "instructions/core-rules";
        path = ../core-rules;
      }
    ]
    ++ (import ./configuration-artifacts.nix {
      inherit
        pkgs
        lib
        hostname
        isDarwin
        ;
    })
    ++ (import ./mcp-artifacts.nix {
      inherit
        pkgs
        lib
        ;
    })
    ++
      lib.mapAttrsToList
        (name: path: {
          name = "workflows/${name}";
          inherit path;
        })
        (
          (import ../skills/writing/page-composer/install { }).workflowSources
          // builtins.listToAttrs (
            map
              (name: {
                inherit name;
                value = ../../harnesses/claude-code/workflows + "/${name}";
              })
              (
                builtins.filter (lib.hasSuffix ".js") (
                  builtins.attrNames (builtins.readDir ../../harnesses/claude-code/workflows)
                )
              )
          )
        );
in
{
  entries = artifactEntries;
  discovery = {
    skills = interactiveSkillNames ++ [
      "core"
      "all-skills"
    ];
    indexedSkills = skillCatalog.indexedSkillNamesFor interactiveSkillNames;
    repositorySkills = skillCatalog.dotfilesRepoSkillNames;
  };
}
