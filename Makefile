.PHONY: all test test-quick test-nix test-modules test-docker test-runtime test-all build shell clean help

all:

test: test-nix

test-quick:
	__tests__/run.sh --quick

test-nix:
	__tests__/run.sh --nix

test-modules:
	bats tests/nix-modules/home-manager.bats

test-docker:
	__tests__/run.sh --docker

test-runtime:
	__tests__/run.sh --runtime

test-all:
	__tests__/run.sh --all

build:
	docker compose --profile modules build

shell:
	docker compose --profile modules run --rm test-modules-eval bash

clean:
	docker compose --profile modules down --rmi local --volumes

help:
	@echo "Available targets:"
	@echo "  make test           - Run nix tests: quick + modules (default)"
	@echo "  make test-quick     - Run quick tests only (skill validation + bin scripts)"
	@echo "  make test-nix       - Run quick + nix eval tests"
	@echo "  make test-modules   - Run homeManagerModules eval tests only"
	@echo "  make test-docker    - Run docker integration tests"
	@echo "  make test-runtime   - Run live service tests"
	@echo "  make test-all       - Run quick + nix + docker tests"
	@echo "  make build          - Build Docker test container"
	@echo "  make shell          - Open shell in test container"
	@echo "  make clean          - Remove Docker test images and volumes"
