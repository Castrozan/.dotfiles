let
  applicationFocusDefaultDenyGuards = import ./application-focus-default-deny-guards.nix;

  chromeBundleIdentifierRegex = "^com\\.google\\.Chrome$";

  chromeIsFrontmostCondition = [
    {
      type = "frontmost_application_if";
      bundle_identifiers = [ chromeBundleIdentifierRegex ];
    }
    (applicationFocusDefaultDenyGuards.makeApplicationFocusDefaultDenyCondition applicationFocusDefaultDenyGuards.applicationFocusVariableNames.chromeBrowserIsFrontmost)
  ];

  closeTabWithControlW = {
    type = "basic";
    from = {
      key_code = "w";
      modifiers = {
        mandatory = [ "control" ];
        optional = [ "any" ];
      };
    };
    to = [
      {
        key_code = "w";
        modifiers = [ "command" ];
      }
    ];
    conditions = chromeIsFrontmostCondition;
  };

  closeWindowWithCommandW = {
    type = "basic";
    from = {
      key_code = "w";
      modifiers = {
        mandatory = [ "command" ];
        optional = [ "any" ];
      };
    };
    to = [
      {
        key_code = "w";
        modifiers = [
          "command"
          "shift"
        ];
      }
    ];
    conditions = chromeIsFrontmostCondition;
  };

  selectTabWithOptionDigit = digitKeyCode: {
    type = "basic";
    from = {
      key_code = digitKeyCode;
      modifiers = {
        mandatory = [ "option" ];
        optional = [ "any" ];
      };
    };
    to = [
      {
        key_code = digitKeyCode;
        modifiers = [ "command" ];
      }
    ];
    conditions = chromeIsFrontmostCondition;
  };

  tabSelectionDigitKeyCodes = [
    "1"
    "2"
    "3"
    "4"
    "5"
    "6"
    "7"
    "8"
    "9"
  ];

  openHistoryWithControlH = {
    type = "basic";
    from = {
      key_code = "h";
      modifiers = {
        mandatory = [ "control" ];
        optional = [ "any" ];
      };
    };
    to = [
      {
        key_code = "y";
        modifiers = [ "command" ];
      }
    ];
    conditions = chromeIsFrontmostCondition;
  };

  openDownloadsWithControlJ = {
    type = "basic";
    from = {
      key_code = "j";
      modifiers = {
        mandatory = [ "control" ];
        optional = [ "any" ];
      };
    };
    to = [
      {
        key_code = "j";
        modifiers = [
          "command"
          "shift"
        ];
      }
    ];
    conditions = chromeIsFrontmostCondition;
  };

  remapControlShiftZoomKeyToCommandZoom = zoomKeyCode: {
    type = "basic";
    from = {
      key_code = zoomKeyCode;
      modifiers = {
        mandatory = [
          "control"
          "shift"
        ];
        optional = [ "any" ];
      };
    };
    to = [
      {
        key_code = zoomKeyCode;
        modifiers = [ "command" ];
      }
    ];
    conditions = chromeIsFrontmostCondition;
  };

  zoomInWithControlShiftEqual = remapControlShiftZoomKeyToCommandZoom "equal_sign";

  zoomOutWithControlShiftHyphen = remapControlShiftZoomKeyToCommandZoom "hyphen";

  passthroughChromePlainControlKeyToPage = keyCode: {
    type = "basic";
    from = {
      key_code = keyCode;
      modifiers = {
        mandatory = [ "control" ];
        optional = [ ];
      };
    };
    to = [
      {
        key_code = keyCode;
        modifiers = [ "control" ];
      }
    ];
    conditions = chromeIsFrontmostCondition;
  };
in
[
  {
    description = "Chrome: Linux-style Ctrl+W closes the tab while Cmd+W closes the window (mirrors Brave's accelerator overrides)";
    manipulators = [
      closeTabWithControlW
      closeWindowWithCommandW
    ];
  }
  {
    description = "Chrome: Option+Digit selects tabs alongside the native Command+Digit (mirrors Brave's Alt+Digit accelerator additions)";
    manipulators = map selectTabWithOptionDigit tabSelectionDigitKeyCodes;
  }
  {
    description = "Chrome: Linux-style Ctrl+H opens history and Ctrl+J opens downloads via the Mac Chromium shortcuts";
    manipulators = [
      openHistoryWithControlH
      openDownloadsWithControlJ
    ];
  }
  {
    description = "Chrome: Ctrl+Shift+= zooms in and Ctrl+Shift+- zooms out via the Mac Command zoom shortcuts (mirrors Brave's zoom accelerator additions, which Chrome cannot carry because it ignores brave.accelerators)";
    manipulators = [
      zoomInWithControlShiftEqual
      zoomOutWithControlShiftHyphen
    ];
  }
  {
    description = "Chrome: pass plain Ctrl+B through to the page as Ctrl+B (pre-empts the Linux-style Ctrl-to-Cmd remap so web apps can use it as a leader key) instead of remapping to Cmd+B (bold); Ctrl+Shift+B still reaches the bookmark bar toggle";
    manipulators = [
      (passthroughChromePlainControlKeyToPage "b")
    ];
  }
]
