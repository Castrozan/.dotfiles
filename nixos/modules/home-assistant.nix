{
  username,
  ...
}:
{
  virtualisation.oci-containers.containers.homeassistant = {
    image = "ghcr.io/home-assistant/home-assistant:stable";
    volumes = [
      "/home/${username}/.homeassistant:/config"
    ];
    extraOptions = [ "--network=host" ];
  };
}
