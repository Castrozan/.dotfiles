FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates xz-utils git jq bats sudo \
    && rm -rf /var/lib/apt/lists/*

ARG TARGETARCH
RUN case "$TARGETARCH" in \
      amd64) installer_architecture=x86_64; installer_checksum=d3c174b95b948ab1744a9a3507599d030bf31a39033305e8769b51c3134daeff ;; \
      arm64) installer_architecture=aarch64; installer_checksum=6b05c29b805e45e761ccf3fc8ca9ff7f03472f0ae2c98ce38ebb1bdb3b568694 ;; \
      *) exit 1 ;; \
    esac \
    && curl --proto '=https' --tlsv1.2 -sSf -L \
      "https://github.com/DeterminateSystems/nix-installer/releases/download/v3.23.2/nix-installer-${installer_architecture}-linux" \
      -o /tmp/nix-installer \
    && printf '%s  %s\n' "$installer_checksum" /tmp/nix-installer | sha256sum --check \
    && chmod 700 /tmp/nix-installer \
    && /tmp/nix-installer install linux --no-confirm --init none \
    && rm /tmp/nix-installer

ENV PATH="/nix/var/nix/profiles/default/bin:${PATH}"

WORKDIR /dotfiles
COPY . .

RUN rm -rf .git \
    && git config --global user.email "test@test.com" \
    && git config --global user.name "Test" \
    && git init -q && git add -A && git commit -q -m "test snapshot"
