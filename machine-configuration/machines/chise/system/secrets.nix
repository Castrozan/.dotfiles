{
  age = {
    identityPaths = [
      "/home/zanoni/.ssh/id_ed25519"
    ];
    secrets = {
      "id_ed25519_phone" = {
        file = ../../../../secrets/infrastructure/id_ed25519_phone.age;
        owner = "zanoni";
        mode = "600";
      };
      "telegram-bot-token" = {
        file = ../../../../secrets/bot-tokens/telegram/telegram-bot-token.age;
        owner = "zanoni";
        mode = "400";
      };
      "nvidia-api-key" = {
        file = ../../../../secrets/api-keys/nvidia-api-key.age;
        owner = "zanoni";
        mode = "400";
      };
      "grid-token-robson" = {
        file = ../../../../secrets/api-keys/grid-token-robson.age;
        owner = "zanoni";
        mode = "400";
      };
      "grid-token-clever" = {
        file = ../../../../secrets/api-keys/grid-token-clever.age;
        owner = "zanoni";
        mode = "400";
      };
      "brave-api-key" = {
        file = ../../../../secrets/api-keys/brave-api-key.age;
        owner = "zanoni";
        mode = "400";
      };
      "tavily-api-key" = {
        file = ../../../../secrets/api-keys/tavily-api-key.age;
        owner = "zanoni";
        mode = "400";
      };
      "grid-hosts" = {
        file = ../../../../secrets/infrastructure/grid-hosts.age;
        owner = "zanoni";
        mode = "400";
      };
      "ssh-hosts" = {
        file = ../../../../secrets/infrastructure/ssh-hosts.age;
        owner = "zanoni";
        mode = "400";
      };
      "telegram-ids" = {
        file = ../../../../secrets/infrastructure/telegram-ids.age;
        owner = "zanoni";
        mode = "400";
      };
      "telegram-bot-token-clever" = {
        file = ../../../../secrets/bot-tokens/telegram/telegram-bot-token-clever.age;
        owner = "zanoni";
        mode = "400";
      };
      "telegram-bot-token-golden" = {
        file = ../../../../secrets/bot-tokens/telegram/telegram-bot-token-golden.age;
        owner = "zanoni";
        mode = "400";
      };
      "telegram-bot-token-jarvis" = {
        file = ../../../../secrets/bot-tokens/telegram/telegram-bot-token-jarvis.age;
        owner = "zanoni";
        mode = "400";
      };
      "gemini-api-key" = {
        file = ../../../../secrets/api-keys/gemini-api-key.age;
        owner = "zanoni";
        mode = "400";
      };
      "discord-bot-token-clever" = {
        file = ../../../../secrets/bot-tokens/discord/discord-bot-token-clever.age;
        owner = "zanoni";
        mode = "400";
      };
      "discord-bot-token-golden" = {
        file = ../../../../secrets/bot-tokens/discord/discord-bot-token-golden.age;
        owner = "zanoni";
        mode = "400";
      };
      "discord-bot-token-jarvis" = {
        file = ../../../../secrets/bot-tokens/discord/discord-bot-token-jarvis.age;
        owner = "zanoni";
        mode = "400";
      };
      "wifi-psk-zanoni" = {
        file = ../../../../secrets/infrastructure/wifi-psk-zanoni.age;
        mode = "400";
      };
      "jarvis-session-connector-credentials" = {
        file = ../../../../secrets/infrastructure/jarvis-session-connector-credentials.age;
        mode = "400";
      };
      "jellyseerr-smtp-app-password" = {
        file = ../../../../secrets/credentials/media/jellyseerr-smtp-app-password.age;
        mode = "400";
      };
      "arr-qbittorrent-password" = {
        file = ../../../../secrets/credentials/media/arr-qbittorrent-password.age;
        mode = "400";
      };
      "arr-radarr-password" = {
        file = ../../../../secrets/credentials/media/arr-radarr-password.age;
        mode = "400";
      };
      "arr-sonarr-password" = {
        file = ../../../../secrets/credentials/media/arr-sonarr-password.age;
        mode = "400";
      };
      "arr-prowlarr-password" = {
        file = ../../../../secrets/credentials/media/arr-prowlarr-password.age;
        mode = "400";
      };
      "arr-bazarr-password" = {
        file = ../../../../secrets/credentials/media/arr-bazarr-password.age;
        mode = "400";
      };
      "arr-samaritano-indexer-apikey" = {
        file = ../../../../secrets/credentials/media/arr-samaritano-indexer-apikey.age;
        mode = "400";
      };
      "jellyfin-admin-api-key" = {
        file = ../../../../secrets/credentials/media/jellyfin-admin-api-key.age;
        owner = "zanoni";
        mode = "400";
      };
      "kavita-admin-api-key" = {
        file = ../../../../secrets/credentials/media/kavita-admin-api-key.age;
        owner = "zanoni";
        mode = "400";
      };
      "suwayomi-extension-repositories" = {
        file = ../../../../secrets/credentials/media/suwayomi-extension-repositories.age;
        owner = "zanoni";
        mode = "400";
      };
      "proton-openvpn-credentials" = {
        file = ../../../../secrets/credentials/proton-vpn/proton-openvpn-credentials.age;
        mode = "400";
      };
      "proton-paraguay-openvpn-config" = {
        file = ../../../../secrets/credentials/proton-vpn/proton-paraguay-openvpn-config.age;
        mode = "400";
      };
    };
  };
}
