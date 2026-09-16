{ pkgs, ... }:
let
  pythonWithCorrectedCocoaMetadata = pkgs.python312.override {
    packageOverrides = _final: previous: {
      pyobjc-core = previous.pyobjc-core.overridePythonAttrs (previousAttributes: {
        patches = (previousAttributes.patches or [ ]) ++ [
          (pkgs.fetchpatch {
            url = "https://github.com/ronaldoussoren/pyobjc/commit/58d6b127f23bfbc62d46d211ed0df11f25b3e36f.patch";
            stripLen = 1;
            hash = "sha256-8+0QOIlrYvHcrSDC2CnWi5jVqsHwHQrvYts0I8XmCmA=";
          })
        ];
      });
    };
  };
  pythonForQuitWindowlessApplicationsDaemon =
    pythonWithCorrectedCocoaMetadata.withPackages
      (packages: [
        packages.pyobjc-core
        packages.pyobjc-framework-Cocoa
        packages.pyobjc-framework-Quartz
      ]);
in
{
  launchd.user.agents.quit-windowless-applications = {
    serviceConfig = {
      Label = "com.dotfiles.quit-windowless-applications";
      ProgramArguments = [
        "${pythonForQuitWindowlessApplicationsDaemon}/bin/python3"
        "${./quit-windowless-applications-daemon}"
      ];
      KeepAlive = true;
      RunAtLoad = true;
      StandardOutPath = "/tmp/quit-windowless-applications.log";
      StandardErrorPath = "/tmp/quit-windowless-applications.log";
    };
  };
}
