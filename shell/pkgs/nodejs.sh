#!/usr/bin/env bash

. "./shell/src/should_install.sh"
. "./shell/src/use_tzdata.sh"

use_tzdata
should_install nodejs
