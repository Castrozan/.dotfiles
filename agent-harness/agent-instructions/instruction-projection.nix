{ pkgs }:
let
  evaluationDirectory = ../quality/evaluations;
  python = pkgs.python312.withPackages (
    import (evaluationDirectory + "/instructions/python-packages.nix")
  );
  project =
    name: manifest:
    let
      usesReplyFormats =
        if manifest ? sourceDirectory then
          toString manifest.sourceDirectory == toString ./skills/writing/humanize
        else
          builtins.any (document: pkgs.lib.hasInfix "{{reply_format}}" document.text) manifest.documents;
    in
    pkgs.runCommand name
      {
        nativeBuildInputs = [ python ];
        PYTHONPATH = evaluationDirectory;
        manifestFile = pkgs.writeText "${name}-manifest.json" (
          builtins.toJSON (
            manifest
            // pkgs.lib.optionalAttrs usesReplyFormats {
              replyFormatConfiguration = builtins.fromJSON (
                builtins.readFile ../hooks/runtime/common/human_facing_reply/reply-formats.json
              );
            }
          )
        );
      }
      ''
        python ${evaluationDirectory}/instructions/instruction_projection.py "$manifestFile" "$out"
      '';
in
{
  inherit python;

  interactiveDestinations =
    { coreInstructionFile, humanizeSkillDirectory }:
    {
      "${toString ./core-rules/core.md}" = coreInstructionFile;
      "${toString ./skills/writing/humanize}" = humanizeSkillDirectory;
    };

  instructionFile =
    {
      name,
      sources,
      deployed ? null,
      destinations,
    }:
    project name {
      inherit deployed destinations;
      documents = map (source: {
        source = toString source;
        text = builtins.readFile source;
      }) sources;
    };

  instructionText =
    {
      name,
      text,
      deployed,
      destinations,
    }:
    project name {
      inherit deployed destinations;
      documents = [
        {
          source = deployed;
          inherit text;
        }
      ];
    };

  skillDirectory =
    {
      source,
      deployed,
      destinations,
    }:
    project "${builtins.baseNameOf source}-instruction-skill" {
      inherit deployed destinations;
      sourceDirectory = source;
      canonicalDirectory = toString source;
    };
}
