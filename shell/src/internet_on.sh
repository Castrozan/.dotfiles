#!/usr/bin/env bash

# Check internet connection
internet_on() {
    curl -s --head http://www.google.com | head -n 1 | grep "HTTP/1.[01] [23].."
}
