# Makefile for managing dotfiles project

# Variables
DOCKER_IMAGE = ubuntu:latest
CONTAINER_NAME = dotfiles-test
WORKDIR = /home/ciuser/.dotfiles
DEPLOY_ON_CONTAINER_SCRIPT="\
    apt-get update && \
    apt-get install adduser sudo -y && \
    useradd -m -s /bin/bash ciuser && \
    passwd -d ciuser && \
    usermod -aG sudo ciuser && \
    sudo su - ciuser -c ' \
        rm -rf /home/ciuser/.bashrc /home/ciuser/.profile && \
		cd /home/ciuser/.dotfiles && \
        yes | bash install.sh && \
        bash test.sh \
    ' \
"
COMPILE_RESULT_SCRIPT = RESULT=$$? && \
	if [ $$RESULT -eq 0 ]; then \
		echo '\n$(shell tput setaf 2)✔ All Tests passed$(shell tput sgr0)'; \
	else \
		echo '\n$(shell tput setaf 1)✘ Test failed$(shell tput sgr0)'; \
		exit '\nOutput code: '$$RESULT; \
	fi

# Default target
.PHONY: all
all: install

# Run installation script
.PHONY: install
install:
	bash install.sh

# Run test suite locally
.PHONY: test
test:
	bash test.sh

# Run tests and install in Docker (CI-like environment)
.PHONY: ci
ci:
	@echo "Starting CI in Docker container..."
	@docker run --rm --name $(CONTAINER_NAME) -v $(shell pwd):$(WORKDIR) \
		-w $(WORKDIR) $(DOCKER_IMAGE) /bin/bash -c ${DEPLOY_ON_CONTAINER_SCRIPT} && \
		$(COMPILE_RESULT_SCRIPT)

# Help command to list targets
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  make        - Run installation script"
	@echo "  make test   - Run tests locally"
	@echo "  make ci     - Run tests and install in Docker (CI-like environment)"
