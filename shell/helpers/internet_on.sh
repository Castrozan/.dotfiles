#!/bin/bash

# Check internet connection
internet_on() {
    ping -c 1 google.com
}