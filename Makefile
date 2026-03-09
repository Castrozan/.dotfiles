.PHONY: all test test-quick test-nix test-modules test-openclaw test-docker test-runtime test-all build shell clean help

all:

test: test-nix

test-quick:
	tests/run.sh --quick

test-nix:
	tests/run.sh --nix

test-modules:
	bats tests/nix-modules/home-manager.bats

test-openclaw:
	bats tests/openclaw/nix-config.bats

test-docker:
	tests/run.sh --docker

test-runtime:
	tests/run.sh --runtime

test-all:
	tests/run.sh --all

build:
	docker compose --profile modules build

shell:
	docker compose --profile modules run --rm test-modules-eval bash

clean:
	docker compose --profile modules down --rmi local --volumes

help:
	@echo "Available targets:"
	@echo "  make test           - Run nix tests: quick + modules + openclaw (default)"
	@echo "  make test-quick     - Run quick tests only (skill validation + bin scripts)"
	@echo "  make test-nix       - Run quick + nix eval tests"
	@echo "  make test-modules   - Run homeManagerModules eval tests only"
	@echo "  make test-openclaw  - Run openclaw nix config tests only"
	@echo "  make test-docker    - Run docker integration tests"
	@echo "  make test-runtime   - Run openclaw live service tests"
	@echo "  make test-all       - Run quick + nix + docker tests"
	@echo "  make build          - Build Docker test container"
	@echo "  make shell          - Open shell in test container"
	@echo "  make clean          - Remove Docker test images and volumes"
