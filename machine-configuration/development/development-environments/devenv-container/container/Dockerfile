FROM ghcr.io/cachix/devenv/devenv@sha256:d45385cfc144d2277949462ef0219ae334b55df5805762b59e66a9a44cefdd2e
USER root
ARG workspace_uid
ARG workspace_gid
RUN sed -i "s/^devenv:x:1000:100:/devenv:x:${workspace_uid}:${workspace_gid}:/" /etc/passwd && sed -i "s/^users:x:100:/users:x:${workspace_gid}:/" /etc/group && chown -R "${workspace_uid}:${workspace_gid}" /nix /home/devenv
ARG workspace_directory
RUN mkdir -p "${workspace_directory}/node_modules" "${workspace_directory}/.devenv" "${workspace_directory}/dist" && chown "${workspace_uid}:${workspace_gid}" "${workspace_directory}/node_modules" "${workspace_directory}/.devenv" "${workspace_directory}/dist"
USER ${workspace_uid}:${workspace_gid}
ENV HOME=/home/devenv NPM_CONFIG_PREFIX=/home/devenv/.local
ENV PATH=/home/devenv/.local/state/nix/profile/bin:/home/devenv/.local/bin:/home/devenv/.nix-profile/bin:${PATH}
