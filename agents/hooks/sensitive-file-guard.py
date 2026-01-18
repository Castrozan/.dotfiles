#!/usr/bin/env python3
"""sensitive-file-guard.py - Warn when editing potentially sensitive files."""

import json
import re
import sys
import os

# File patterns that often contain secrets or sensitive data
SENSITIVE_PATTERNS = [
    (r"\.env($|\.)", "Environment file - may contain API keys and secrets"),
    (r"\.(pem|key|crt|p12|pfx)$", "Cryptographic key or certificate"),
    (r"secrets?\.(ya?ml|json|toml|nix)$", "Secrets configuration file"),
    (r"credentials?\.(ya?ml|json|toml)$", "Credentials file"),
    (r"\.ssh/(id_|config|known_hosts)", "SSH configuration or keys"),
    (r"(password|passwd|auth)", "File may contain authentication data"),
    (r"\.agenix($|/)", "Agenix encrypted secrets"),
    (r"secrets/.*\.age$", "Age-encrypted secret file"),
    (r"\.gpg$", "GPG encrypted file"),
    (r"\.vault$", "HashiCorp Vault file"),
    (r"(token|jwt|bearer)", "Authentication token file"),
    (r"\.netrc$", "Network authentication file"),
    (r"\.authinfo$", "Authentication info file"),
]

# Additional patterns specific to development
DEV_SENSITIVE_PATTERNS = [
    (r"config/database\.ya?ml", "Database configuration with credentials"),
    (r"\.aws/(credentials|config)", "AWS credentials"),
    (r"\.gcp/", "Google Cloud credentials"),
    (r"\.kube/config", "Kubernetes cluster credentials"),
    (r"docker-compose.*\.ya?ml.*environment", "Docker compose with environment secrets"),
    (r"\.dockercfg", "Docker registry credentials"),
]

def check_file_content_sensitivity(file_path: str) -> list[str]:
    """Check if file content contains sensitive patterns."""
    warnings = []
    try:
        # Only read first 1KB to check for patterns
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(1024).lower()

        sensitive_keywords = [
            'password', 'secret', 'api_key', 'token', 'private_key',
            'client_secret', 'auth_token', 'bearer', 'credentials'
        ]

        found_keywords = [kw for kw in sensitive_keywords if kw in content]
        if found_keywords:
            warnings.append(f"Content contains sensitive keywords: {', '.join(found_keywords)}")

    except (IOError, UnicodeDecodeError):
        pass

    return warnings

def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    file_path = data.get("tool_input", {}).get("file_path", "")

    if not file_path:
        sys.exit(0)

    warnings = []

    # Check filename patterns
    all_patterns = SENSITIVE_PATTERNS + DEV_SENSITIVE_PATTERNS
    for pattern, message in all_patterns:
        if re.search(pattern, file_path, re.IGNORECASE):
            warnings.append(f"🔒 SENSITIVE FILE: {message}")
            break

    # For existing files, also check content
    if os.path.exists(file_path) and os.path.isfile(file_path):
        content_warnings = check_file_content_sensitivity(file_path)
        warnings.extend([f"🔒 {w}" for w in content_warnings])

    if warnings:
        reminder = "\n💡 Remember to review changes before committing and consider using git-crypt or agenix for secrets."
        output = {
            "continue": True,
            "systemMessage": "\n".join(warnings) + reminder
        }
        print(json.dumps(output))

    sys.exit(0)

if __name__ == "__main__":
    main()