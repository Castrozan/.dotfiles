{
  self,
  helpers,
  lib,
  ...
}:
let
  chiseHomePackageNames = map lib.getName self.nixosConfigurations.chise.config.home-manager.users.zanoni.home.packages;
in
{
  domain-chatgpt-sandbox-finds-bubblewrap-on-the-user-path =
    helpers.mkEvalCheck "domain-chatgpt-sandbox-finds-bubblewrap-on-the-user-path"
      (
        lib.elem "bubblewrap" chiseHomePackageNames
        && lib.elem "chatgpt-resource-managed" chiseHomePackageNames
      )
      "ChatGPT's Codex runtime takes PATH from the login shell, so bubblewrap must be a home package wherever the app is installed";
}
