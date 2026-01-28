# Shared utilities for opencode module
{
  # Color name to hex mapping (for OpenCode compatibility)
  # OpenCode expects hex color format (#RRGGBB) in agent frontmatter,
  # but source agents use color names for Claude compatibility.
  colorNameToHex = {
    red = "#FF0000";
    green = "#00FF00";
    blue = "#0000FF";
    cyan = "#00FFFF";
    magenta = "#FF00FF";
    yellow = "#FFFF00";
    orange = "#FFA500";
    purple = "#800080";
    pink = "#FFC0CB";
    white = "#FFFFFF";
    black = "#000000";
    gray = "#808080";
    grey = "#808080";
  };

  # Process agent file: convert color names to hex in frontmatter
  processAgentFile =
    colorMap: content:
    builtins.replaceStrings (map (name: "color: ${name}") (builtins.attrNames colorMap)) (map (
      name: "color: \"${colorMap.${name}}\""
    ) (builtins.attrNames colorMap)) content;
}
