{ pkgs }:
scriptPath:
let
  scriptName = builtins.baseNameOf scriptPath;
  shellScript = pkgs.writeShellScript scriptName (builtins.readFile scriptPath);
in
pkgs.runCommandCC "${scriptName}-setuid-root-wrapper" { } ''
  cat > main.c << 'WRAPPER_SOURCE'
  #include <unistd.h>
  #include <stdio.h>
  extern char **environ;
  int main(int argc, char **argv) {
    if (setuid(0) != 0) { perror("setuid"); return 1; }
    if (setgid(0) != 0) { perror("setgid"); return 1; }
    argv[0] = "${shellScript}";
    execve("${shellScript}", argv, environ);
    perror("execve");
    return 1;
  }
  WRAPPER_SOURCE
  $CC -o $out main.c
''
