# Phone SSH Config Setup

To use `ssh zanoni` from your phone, create an SSH config file on your phone.

## Quick Setup

Connect to Tailscale

On your phone (Termux), run:

```bash
# Create .ssh directory if it doesn't exist
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Create SSH config file
cat > ~/.ssh/config << 'EOF'
Host zanoni
    HostName 100.94.11.81
    User zanoni
    IdentityFile ~/.ssh/id_ed25519
    # Optional: Add your PC's host key to avoid prompts
    # StrictHostKeyChecking accept-new
EOF

# Set correct permissions
chmod 600 ~/.ssh/config
```

## Now you can use:

```bash
# Instead of: ssh zanoni@100.94.11.81
ssh zanoni
```

## Verify It Works

```bash
ssh zanoni

```
