# syntax=docker/dockerfile:1
FROM gradle:8.10.2-jdk21@sha256:963d59f7f22767da4efbcf46b661361b61af5fb88b0309da1071c4234c647eba AS build
USER root
WORKDIR /src
ADD --checksum=sha256:238a4b91d40f0c32d2096475c1a7bdf6500096272ea776ae6f0565c919b31b44 https://github.com/miwayomi/miwayomi/archive/bf18765a00cfc639ead84d97e071383c436ca7d7.tar.gz /tmp/miwayomi.tar.gz
RUN tar --extract --gzip --file /tmp/miwayomi.tar.gz --strip-components 1 --directory /src
COPY miwayomi-manga-input-initialization.patch /tmp/miwayomi-manga-input-initialization.patch
RUN git apply /tmp/miwayomi-manga-input-initialization.patch
RUN gradle --no-daemon --console=plain :server:shadowJar

FROM ghcr.io/miwayomi/miwayomi:0.2.9@sha256:8e7094088565b97091319dfa92b80a8c22497a712e72af09e2470454f5942ec4
COPY --from=build --chown=10001:10001 /src/server/build/libs/miwayomi-all.jar /app/miwayomi-all.jar
