# Playwright Browser Path Fix for NixOS

## Problem Description

When using Playwright with NixOS, you may encounter the error:
```
Error: browserType.launch: Executable doesn't exist at /nix/store/[hash]-playwright-browsers/chromium_headless_shell-[version]/chrome-linux/headless_shell
```

This happens because:
1. The browser path in your project points to an outdated nix store path
2. There's a version mismatch between what Playwright expects and what's available
3. The browser executables are not properly symlinked

## Identifying the Issue

### Step 1: Check Current Browser Path
```bash
# Check what path your project is using
cat package.json | grep PLAYWRIGHT_BROWSERS_PATH

# Check if that path exists
ls -la /nix/store/[your-hash]-playwright-browsers
```

### Step 2: Find Available Browser Packages
```bash
# List all playwright-related packages in nix store
ls /nix/store/ | grep playwright

# Find current system references
nix-store -q --references /run/current-system/sw | grep playwright
```

### Step 3: Check Browser Version Mismatch
```bash
# Check what browser versions are available
ls -la /nix/store/[correct-hash]-playwright-browsers/

# Common issue: chromium_headless_shell-1155 vs chromium_headless_shell-1179
```

## The Fix

### Step 1: Create a Corrected Browser Directory
```bash
# Create a permanent directory for the fix
mkdir -p ~/.local/share/playwright-browsers
cd ~/.local/share/playwright-browsers

# Copy the current browser structure
cp -r /nix/store/[current-hash]-playwright-browsers/* .

# Create the missing version symlink (adjust versions as needed)
ln -sf /nix/store/[hash]-playwright-chromium-headless-shell chromium_headless_shell-1155
```

### Step 2: Update Your Project Configuration
In your `package.json`, update the test script:
```json
{
  "scripts": {
    "test": "export PLAYWRIGHT_BROWSERS_PATH=/home/zanoni/.local/share/playwright-browsers && export PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=true && npx playwright test --project chromium --timeout 10000"
  }
}
```

### Step 3: Verify the Fix
```bash
# Test that the browser executable exists
ls -la ~/.local/share/playwright-browsers/chromium_headless_shell-1155/chrome-linux/headless_shell

# Run your tests
npm test
```

## Finding the Correct Store Paths

### Method 1: System References
```bash
# Find playwright packages in current system
nix-store -q --references /run/current-system/sw | grep playwright
```

### Method 2: Search Store
```bash
# Search for all playwright packages
ls /nix/store/ | grep playwright-browsers

# Check the most recent one
ls -la /nix/store/[latest-hash]-playwright-browsers/
```

### Method 3: Check Browser Structure
```bash
# Verify the browser executable exists
ls -la /nix/store/[hash]-playwright-chromium-headless-shell/chrome-linux/headless_shell
```

## Prevention Tips

1. **Use Relative Paths**: Instead of hardcoding nix store paths, use a permanent location like `~/.local/share/playwright-browsers`

2. **Version Flexibility**: Create symlinks for multiple versions:
   ```bash
   ln -sf target chromium_headless_shell-1155
   ln -sf target chromium_headless_shell-1179
   ```

3. **Regular Updates**: When updating your system, check if browser paths need updating:
   ```bash
   # After nixos-rebuild switch
   ls /nix/store/ | grep playwright-browsers | tail -1
   ```

4. **Environment Variables**: Use environment variables for flexibility:
   ```bash
   export PLAYWRIGHT_BROWSERS_PATH="/home/zanoni/.local/share/playwright-browsers"
   export PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=true
   ```

## Troubleshooting

### If browsers are still not found:
1. Check permissions: `chmod +x ~/.local/share/playwright-browsers/*/chrome-linux/headless_shell`
2. Verify symlinks: `ls -la ~/.local/share/playwright-browsers/`
3. Check the exact version Playwright is looking for in the error message

### If tests fail with other errors:
1. Try running a single test: `npx playwright test --project chromium --max-failures=1`
2. Check if the web application is running: `npm run start`
3. Verify the playwright config: `cat playwright.config.js`

## NixOS-Specific Notes

1. **Nix Store Immutability**: Never modify files directly in `/nix/store/` - they are read-only
2. **Garbage Collection**: Nix may garbage collect old store paths, breaking hardcoded references
3. **System Updates**: After `nixos-rebuild switch`, browser paths may change

## Quick Fix Command

For future issues, you can use this one-liner to fix the browser path:
```bash
# Find current browser path and create fix
CURRENT_BROWSERS=$(nix-store -q --references /run/current-system/sw | grep playwright-browsers | head -1)
mkdir -p ~/.local/share/playwright-browsers
cp -r $CURRENT_BROWSERS/* ~/.local/share/playwright-browsers/
# Then manually add missing version symlinks as needed
```

## Final Solution Applied

The permanent fix implemented:
1. Created `~/.local/share/playwright-browsers` with corrected browser structure
2. Updated `package.json` to use the permanent path
3. Added missing version symlinks for chromium_headless_shell
4. All tests now pass consistently (11/11 ✅)

This approach ensures the fix survives system updates and nix garbage collection.

## Example: Actual Fix Applied (2025-07-12)

**Problem**: Tests were looking for `chromium_headless_shell-1155` but system had `chromium_headless_shell-1179`

**Solution**:
```bash
# Found current browser path
nix-store -q --references /run/current-system/sw | grep playwright
# Result: /nix/store/704w99kx75y1kicjkdyn03xk2hh4svzc-playwright-browsers

# Created permanent fix directory
mkdir -p ~/.local/share/playwright-browsers
cp -r /nix/store/704w99kx75y1kicjkdyn03xk2hh4svzc-playwright-browsers/* ~/.local/share/playwright-browsers/

# Added missing version symlink
ln -sf /nix/store/dyibrj0anhm45dbcl6acwj0qwj4ka5jz-playwright-chromium-headless-shell ~/.local/share/playwright-browsers/chromium_headless_shell-1155

# Updated package.json
"test": "export PLAYWRIGHT_BROWSERS_PATH=/home/zanoni/.local/share/playwright-browsers && export PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=true && npx playwright test --project chromium --timeout 10000"
```

**Result**: All 11 tests now pass consistently ✅ 