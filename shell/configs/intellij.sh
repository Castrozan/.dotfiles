#!/usr/bin/env bash

# Export Intellij to PATH
if [ -d "/opt/idea-IU-*" ]; then
    export PATH="$PATH:/opt/idea-IU-*/bin"
fi
