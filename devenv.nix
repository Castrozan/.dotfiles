{ pkgs, ... }:

{
  packages = [
    pkgs.python312
    pkgs.postgresql_16
  ];

  services.postgres = {
    enable = true;
    package = pkgs.postgresql_16;
    initialDatabases = [ { name = "dev"; } ];
  };

  env.PGHOST = "localhost";
  env.PGUSER = "postgres";
}
