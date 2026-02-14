FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates xz-utils git jq bats sudo \
    && rm -rf /var/lib/apt/lists/*

RUN curl --proto '=https' --tlsv1.2 -sSf -L \
    https://install.determinate.systems/nix \
    | sh -s -- install linux --no-confirm --init none

ENV PATH="/nix/var/nix/profiles/default/bin:${PATH}"

WORKDIR /dotfiles
COPY . .

RUN rm -rf .git \
    && git config --global user.email "test@test.com" \
    && git config --global user.name "Test" \
    && git init -q && git add -A && git commit -q -m "test snapshot"

CMD ["bats", "tests/modules/eval.bats"]
