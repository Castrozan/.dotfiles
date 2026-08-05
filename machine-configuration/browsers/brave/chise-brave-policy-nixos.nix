_: {
  environment.etc."brave/policies/managed/dotfiles-managed-policies.json".text = builtins.toJSON {
    PasswordManagerEnabled = false;
  };
}
