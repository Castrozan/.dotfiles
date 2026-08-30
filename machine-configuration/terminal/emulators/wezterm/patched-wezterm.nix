{ latest }:
latest.wezterm.overrideAttrs (previousAttributes: {
  patches = (previousAttributes.patches or [ ]) ++ [
    ./wezterm-patches/hide-quick-select-help-row.patch
  ];
})
