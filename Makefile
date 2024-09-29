# Makefile for managing dotfiles project

# Variables
DOCKER_IMAGE = ubuntu:latest
CONTAINER_NAME = dotfiles-test
WORKDIR = /root/.dotfiles_ubuntu

# Default target
.PHONY: all
all: install

# Run installation script
.PHONY: install
install:
	sh install.sh

# Run test suite locally
.PHONY: test
test:
	sh test.sh

# Run tests and install in Docker (CI-like environment)
.PHONY: ci
ci:
	@echo "Starting CI in Docker container..."
	@docker rm -f $(CONTAINER_NAME) >/dev/null 2>&1 || true
	@docker run --name $(CONTAINER_NAME) -v $(shell pwd):$(WORKDIR) -w $(WORKDIR) $(DOCKER_IMAGE) /bin/bash -c "\
		apt-get update && \
		rm -rf /root/.bashrc /root/.profile && \
		yes | sh install.sh && \
		source /root/.bashrc && \
		sh test.sh" && \
		RESULT=$$? && \
		if [ $$RESULT -eq 0 ]; then \
			echo '\n$(shell tput setaf 2)✔ All Tests passed$(shell tput sgr0)'; \
		else \
			echo '\n$(shell tput setaf 1)✘ Test failed$(shell tput sgr0)'; \
			exit '\nOutput code: '$$RESULT; \
		fi

# Help command to list targets
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  make        - Run installation script"
	@echo "  make test   - Run tests locally"
	@echo "  make clean  - Clean temporary files"
