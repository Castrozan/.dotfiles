{
  age = {
    identityPaths = [
      "/home/zanoni/.ssh/id_ed25519"
    ];
    secrets = {
      "id_ed25519_phone" = {
        file = ../../secrets/infrastructure/id_ed25519_phone.age;
        owner = "zanoni";
        mode = "600";
      };
      "telegram-bot-token" = {
        file = ../../secrets/bot-tokens/telegram-bot-token.age;
        owner = "zanoni";
        mode = "400";
      };
      "nvidia-api-key" = {
        file = ../../secrets/api-keys/nvidia-api-key.age;
        owner = "zanoni";
        mode = "400";
      };
      "grid-token-robson" = {
        file = ../../secrets/api-keys/grid-token-robson.age;
        owner = "zanoni";
        mode = "400";
      };
      "grid-token-clever" = {
        file = ../../secrets/api-keys/grid-token-clever.age;
        owner = "zanoni";
        mode = "400";
      };
      "brave-api-key" = {
        file = ../../secrets/api-keys/brave-api-key.age;
        owner = "zanoni";
        mode = "400";
      };
      "tavily-api-key" = {
        file = ../../secrets/api-keys/tavily-api-key.age;
        owner = "zanoni";
        mode = "400";
      };
      "grid-hosts" = {
        file = ../../secrets/infrastructure/grid-hosts.age;
        owner = "zanoni";
        mode = "400";
      };
      "ssh-hosts" = {
        file = ../../secrets/infrastructure/ssh-hosts.age;
        owner = "zanoni";
        mode = "400";
      };
      "telegram-ids" = {
        file = ../../secrets/infrastructure/telegram-ids.age;
        owner = "zanoni";
        mode = "400";
      };
      "telegram-bot-token-clever" = {
        file = ../../secrets/bot-tokens/telegram-bot-token-clever.age;
        owner = "zanoni";
        mode = "400";
      };
      "telegram-bot-token-golden" = {
        file = ../../secrets/bot-tokens/telegram-bot-token-golden.age;
        owner = "zanoni";
        mode = "400";
      };
      "telegram-bot-token-jarvis" = {
        file = ../../secrets/bot-tokens/telegram-bot-token-jarvis.age;
        owner = "zanoni";
        mode = "400";
      };
      "gemini-api-key" = {
        file = ../../secrets/api-keys/gemini-api-key.age;
        owner = "zanoni";
        mode = "400";
      };
      "discord-bot-token-clever" = {
        file = ../../secrets/bot-tokens/discord-bot-token-clever.age;
        owner = "zanoni";
        mode = "400";
      };
      "discord-bot-token-golden" = {
        file = ../../secrets/bot-tokens/discord-bot-token-golden.age;
        owner = "zanoni";
        mode = "400";
      };
      "discord-bot-token-jarvis" = {
        file = ../../secrets/bot-tokens/discord-bot-token-jarvis.age;
        owner = "zanoni";
        mode = "400";
      };
      "wifi-psk-zanoni" = {
        file = ../../secrets/infrastructure/wifi-psk-zanoni.age;
        mode = "400";
      };
      "jarvis-session-connector-credentials" = {
        file = ../../secrets/infrastructure/jarvis-session-connector-credentials.age;
        mode = "400";
      };
      "jellyseerr-smtp-app-password" = {
        file = ../../secrets/credentials/jellyseerr-smtp-app-password.age;
        mode = "400";
      };
      "arr-qbittorrent-password" = {
        file = ../../secrets/credentials/arr-qbittorrent-password.age;
        mode = "400";
      };
      "arr-radarr-password" = {
        file = ../../secrets/credentials/arr-radarr-password.age;
        mode = "400";
      };
      "arr-sonarr-password" = {
        file = ../../secrets/credentials/arr-sonarr-password.age;
        mode = "400";
      };
      "arr-prowlarr-password" = {
        file = ../../secrets/credentials/arr-prowlarr-password.age;
        mode = "400";
      };
      "arr-samaritano-indexer-apikey" = {
        file = ../../secrets/credentials/arr-samaritano-indexer-apikey.age;
        mode = "400";
      };
      "jellyfin-admin-api-key" = {
        file = ../../secrets/credentials/jellyfin-admin-api-key.age;
        owner = "zanoni";
        mode = "400";
      };
    };
  };
}
