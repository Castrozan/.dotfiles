# Makefile for managing dotfiles project

# Default target
.PHONY: all
all:

# Creates and configs .shell_env_vars file
.PHONY: env_vars
env_vars:
	git update-index --skip-worktree .shell_env_vars

# Help command to list targets
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  make - Does nothing"
	@echo "  make env_vars - Creates and configs .shell_env_vars file"
