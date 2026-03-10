# Active Work

## Python Migration: Hyprland Window Scripts
- **Objective**: Migrate `home/modules/hyprland/scripts/windows/` from bash to Python 3.12
- **Why**: Scripts are unreliable due to bash's poor JSON handling, state management, and error propagation
- **Steps**:
  1. Create shared `hyprland_ipc.py` library
  2. Migrate all 9 window scripts to Python
  3. Create pytest tests with mocked hyprctl
  4. Update `scripts.nix` with Python packaging
  5. Integrate pytest into test runner
  6. Document migration policy in dotfiles skill
  7. Remove old bash scripts
  8. Rebuild and verify
