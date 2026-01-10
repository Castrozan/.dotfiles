# keyd keyboard remapping daemon configuration
{ ... }:
let
  # Base keyd configuration with layer definitions
  defaultConf = ''
    [ids]
    *

    [main]
    # Global key mappings can go here
    
    # TEST KEYBIND: Super+U activates test_layer (works everywhere, no app detection needed)
    # Press Super+U, then press 'a' to test - it should send Ctrl+A (select all)
    meta.u = layer(test_layer)
    
    [test_layer]
    # Easy test: Super+U then 'a' = Ctrl+A (select all - you'll see text get selected)
    a = C-a
    # Super+U then 's' = Ctrl+S (save)
    s = C-s
    # Super+U then 'c' = Ctrl+C (copy)
    c = C-c

    # Obsidian layer definitions
    [obsidian_layer]
    # While in obsidian_layer, map keys to commands
    a = C-a
    s = C-s
    f = C-f
    n = C-n
    o = C-o
    p = C-p
    w = C-w
    z = C-z
    y = C-y
    x = C-x
    c = C-c
    v = C-v

    # Brave layer definitions
    [brave_layer]
    # While in brave_layer, map keys to commands
    t = C-t
    w = C-w
    r = C-r
    n = C-n
    shift-n = C-S-n
    shift-t = C-S-t
    shift-w = C-S-w
    l = C-l
    k = C-k
    shift-k = C-S-k
    d = C-d
    shift-d = C-S-d
    h = C-h
    j = C-j
    shift-j = C-S-j
  '';
in
{
  # Enable keyd service
  services.keyd = {
    enable = true;
  };

  # Write keyd configuration to /etc/keyd/default.conf
  # keyd reads from /etc/keyd/default.conf by default
  environment.etc."keyd/default.conf" = {
    text = defaultConf;
    mode = "0644";
  };

  # Add user to keyd group for application-specific remapping
  # Note: username is hardcoded as this is a user-specific module
  users.users.zanoni.extraGroups = [ "keyd" ];

  # Load uinput kernel module (required for keyd)
  boot.kernelModules = [ "uinput" ];
}

