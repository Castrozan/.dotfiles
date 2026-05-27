{
  stdenv,
  lib,
  aerospaceSource,
}:
let
  version = "0.20.3-Beta-castrozan-fix";
  infoPlist = ''
    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
    <plist version="1.0">
    <dict>
      <key>CFBundleDevelopmentRegion</key>
      <string>en</string>
      <key>CFBundleExecutable</key>
      <string>AeroSpace</string>
      <key>CFBundleIdentifier</key>
      <string>bobko.aerospace</string>
      <key>CFBundleInfoDictionaryVersion</key>
      <string>6.0</string>
      <key>CFBundleName</key>
      <string>AeroSpace</string>
      <key>CFBundlePackageType</key>
      <string>APPL</string>
      <key>CFBundleShortVersionString</key>
      <string>${version}</string>
      <key>CFBundleVersion</key>
      <string>${version}</string>
      <key>LSMinimumSystemVersion</key>
      <string>13.0</string>
      <key>LSUIElement</key>
      <true/>
    </dict>
    </plist>
  '';
in
stdenv.mkDerivation {
  pname = "aerospace";
  inherit version;

  src = aerospaceSource;

  __noChroot = true;

  dontConfigure = true;

  buildPhase = ''
    runHook preBuild

    export HOME=$TMPDIR/home
    mkdir -p $HOME
    export PATH=/usr/bin:/bin:/usr/sbin:/sbin:$PATH

    cat > Sources/Common/versionGenerated.swift <<'SWIFT_EOF'
    public let aeroSpaceAppVersion = "${version}"
    SWIFT_EOF

    cat > Sources/Common/gitHashGenerated.swift <<'SWIFT_EOF'
    public let gitHash = "castrozan-fix"
    public let gitShortHash = "castro"
    SWIFT_EOF

    cat > Sources/Cli/subcommandDescriptionsGenerated.swift <<'SWIFT_EOF'
    let subcommandDescriptions: [[String]] = []
    SWIFT_EOF

    /Library/Developer/CommandLineTools/usr/bin/swift build -c release --arch arm64 --arch x86_64 --product aerospace
    /Library/Developer/CommandLineTools/usr/bin/swift build -c release --arch arm64 --arch x86_64 --product AeroSpaceApp

    runHook postBuild
  '';

  installPhase = ''
        runHook preInstall

        mkdir -p $out/bin
        cp .build/apple/Products/Release/aerospace $out/bin/aerospace

        appBundleDirectory=$out/Applications/AeroSpace.app
        mkdir -p $appBundleDirectory/Contents/MacOS $appBundleDirectory/Contents/Resources
        cp .build/apple/Products/Release/AeroSpaceApp $appBundleDirectory/Contents/MacOS/AeroSpace
        cp docs/config-examples/default-config.toml $appBundleDirectory/Contents/Resources/ || true

        cat > $appBundleDirectory/Contents/Info.plist <<'PLIST_EOF'
    ${infoPlist}
        PLIST_EOF

        /usr/bin/codesign --force --deep --sign - $appBundleDirectory

        runHook postInstall
  '';

  meta = {
    description = "Castrozan fork of AeroSpace with macOS 26 Tahoe AX prompt-loop fix";
    homepage = "https://github.com/Castrozan/AeroSpace";
    license = lib.licenses.mit;
    platforms = [
      "aarch64-darwin"
      "x86_64-darwin"
    ];
    mainProgram = "aerospace";
  };
}
