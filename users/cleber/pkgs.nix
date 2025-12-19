{
  pkgs,
  latest,
  ...
}:
{
  home.packages =
    with pkgs;
    [
      fastfetch
      insomnia
      kubectl
      micronaut
      nixd
      nixfmt-rfc-style
      nodejs
      postman
      redisinsight
    ]
    # Appending to list
    ++ (with latest; [
      lazydocker
    ]);
}
