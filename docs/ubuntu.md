# Ubuntu Setup Guide

This guide explains how to deploy the Ubuntu configuration from this repository. The setup is driven by an interactive installation script that installs necessary applications and configures dotfiles to create a tailored development environment.

## Prerequisites

- **Ubuntu System:** Tested on recent versions (22.04); ensure your system is up to date.
- **Repository Location:** Clone this repository into your home directory for easy access.

## Steps to Deploy

### 1. **Clone the repo into your home directory.**

### 2. Run the Installer

The installation script is interactive and will guide you through the process. Simply execute:
```bash
make install
```

### 3. Customize with Flags

If you prefer a more declarative approach, you can use the `-d` flag. This tells the installer to follow the configuration specified in the `declarative.sh` file, allowing you to install only the specific dotfiles and packages you want:
```bash
make install -d
```
