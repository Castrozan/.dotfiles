.PHONY: all test test-modules test-openclaw test-docker build shell clean env_vars help

all:

test: test-modules test-openclaw

test-modules:
	bats tests/modules/eval.bats

test-openclaw:
	bats tests/openclaw/eval.bats

test-docker:
	docker compose --profile modules up --build --abort-on-container-exit

build:
	docker compose --profile modules build

shell:
	docker compose --profile modules run --rm test-modules-eval bash

clean:
	docker compose --profile modules down --rmi local --volumes

env_vars:
	git update-index --skip-worktree .shell_env_vars

help:
	@echo "Available targets:"
	@echo "  make test           - Run all local tests (modules + openclaw)"
	@echo "  make test-modules   - Run homeManagerModules eval tests"
	@echo "  make test-openclaw  - Run openclaw eval tests"
	@echo "  make test-docker    - Run module tests in Docker container"
	@echo "  make build          - Build Docker test container"
	@echo "  make shell          - Open shell in test container"
	@echo "  make clean          - Remove Docker test images and volumes"
	@echo "  make env_vars       - Configure .shell_env_vars file"
