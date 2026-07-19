{ lib }:
let
  privatePrunedConfigSubstringsPath = ../../../private-config/claude/prohibited-words.txt;
in
if builtins.pathExists privatePrunedConfigSubstringsPath then
  lib.filter (line: line != "" && !(lib.hasPrefix "#" line)) (
    lib.splitString "\n" (builtins.readFile privatePrunedConfigSubstringsPath)
  )
else
  [ ]
