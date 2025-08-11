{ pkgs, ... }:
let
  # Absolute path to the pipx binary provided by Nix. This avoids relying on PATH
  # during the activation script, where the new profile might not yet be sourced.
  pipxBin = "${pkgs.python311Packages.pipx}/bin/pipx";
in
{
  # Ensure this module runs after pipx has been set up so that the `pipx` command is available.
  home.activation.installDooit = {
    # `pipxSetup` is defined in the pipx.nix module, so we run after it.
    after = [ "pipxSetup" ];
    # No specific ordering requirements before other steps.
    before = [ ];
    # The shell snippet that installs the package if it hasn't been already.
    data = ''
      pipx_bin="${pipxBin}"

      # Abort early if pipx binary is unavailable for some reason.
      if ! [ -x "$pipx_bin" ]; then
        echo "pipx binary not found at $pipx_bin; skipping dooit installation." >&2
        exit 0
      fi

      # Install dooit only if it is not yet installed.
      if ! "$pipx_bin" list | grep -qE "\bdooit\b"; then
        echo "Installing dooit via pipx..."
        "$pipx_bin" install dooit
      else
        echo "dooit is already installed via pipx."
      fi
    '';
  };
}
