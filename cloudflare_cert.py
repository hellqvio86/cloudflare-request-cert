#!/usr/bin/env python3
"""
Cloudflare Request Cert - SSL/TLS certificate automation using Cloudflare DNS
"""
import logging
import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import Optional


def load_env_file(env_file: Path) -> dict[str, str]:
    """Load environment variables from a .env file."""
    env_vars = {}
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, _, value = line.partition("=")
                    env_vars[key.strip()] = value.strip().strip("\"'")
    logging.debug("Loaded environment variables: %s", env_vars)

    return env_vars


def validate_credentials(api_token: Optional[str]) -> bool:
    """Validate that required credentials are present."""
    if not api_token:
        print("Error: CLOUDFLARE_API_TOKEN is required", file=sys.stderr)
        print("\nPlease set it in one of these ways:", file=sys.stderr)
        print("1. Create a .env file with: CLOUDFLARE_API_TOKEN=your_token", file=sys.stderr)
        print("2. Export it: export CLOUDFLARE_API_TOKEN=your_token", file=sys.stderr)
        return False
    return True


def request_certificate(
    domain: str,
    email: str,
    api_token: str,
    staging: bool = False,
    propagation_seconds: int = 10,
) -> int:
    """Request or renew a certificate using certbot with Cloudflare DNS."""

    # Prepare credentials file
    credentials_dir = Path.home() / ".secrets" / "certbot"
    credentials_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    credentials_file = credentials_dir / "cloudflare.ini"

    # Write credentials
    credentials_file.write_text(f"dns_cloudflare_api_token = {api_token}\n")
    credentials_file.chmod(0o600)

    # Build certbot command
    cmd = [
        "certbot",
        "certonly",
        "--dns-cloudflare",
        "--dns-cloudflare-credentials",
        str(credentials_file),
        "--dns-cloudflare-propagation-seconds",
        str(propagation_seconds),
        "-d",
        domain,
        "--email",
        email,
        "--agree-tos",
        "--non-interactive",
    ]

    if staging:
        cmd.extend(["--staging"])

    print(f"Requesting certificate for {domain}...")
    print(f"Using Cloudflare API (propagation wait: {propagation_seconds}s)")
    if staging:
        print("⚠️  Using STAGING environment (test certificates)")

    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"\n✓ Certificate successfully obtained for {domain}")
        print(f"Certificate location: /etc/letsencrypt/live/{domain}/")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Failed to obtain certificate: {e}", file=sys.stderr)
        return 1
    except FileNotFoundError:
        print("\n✗ certbot not found. Please install it first:", file=sys.stderr)
        print("  make install", file=sys.stderr)
        return 1
    finally:
        # Clean up credentials file
        if credentials_file.exists():
            credentials_file.unlink()


def main():
    parser = argparse.ArgumentParser(
        description="Request SSL/TLS certificates using Cloudflare DNS"
    )
    parser.add_argument(
        "-d",
        "--domain",
        help="Domain name to request certificate for (can also be set in .env as DOMAIN)",
    )
    parser.add_argument(
        "-e",
        "--email",
        help="Email address for certificate notifications (can also be set in .env as EMAIL)",
    )
    parser.add_argument(
        "--staging",
        action="store_true",
        help="Use Let's Encrypt staging server (for testing, can also be set in .env as STAGING=1)",
    )
    parser.add_argument(
        "--propagation-seconds",
        type=int,
        help="DNS propagation wait time in seconds (default: 10, can also be set in .env)",
    )
    parser.add_argument(
        "--env-file", type=Path, default=Path(".env"), help="Path to .env file (default: .env)"
    )

    args = parser.parse_args()

    # Load environment variables
    env_vars = load_env_file(args.env_file)

    # Get values from args or env vars, with args taking precedence
    domain = args.domain or env_vars.get("DOMAIN") or os.getenv("DOMAIN")
    email = args.email or env_vars.get("EMAIL") or os.getenv("EMAIL")
    api_token = env_vars.get("CLOUDFLARE_API_TOKEN") or os.getenv("CLOUDFLARE_API_TOKEN")
    staging = args.staging or env_vars.get("STAGING") == "1" or os.getenv("STAGING") == "1"
    propagation_seconds = (
        args.propagation_seconds or int(env_vars.get("PROPAGATION_SECONDS", "10"))
        if env_vars.get("PROPAGATION_SECONDS")
        else 10
    )

    # Validate required parameters
    if not domain:
        print("Error: DOMAIN is required", file=sys.stderr)
        print("Set it via -d/--domain argument or in .env file", file=sys.stderr)
        return 1

    if not email:
        print("Error: EMAIL is required", file=sys.stderr)
        print("Set it via -e/--email argument or in .env file", file=sys.stderr)
        return 1

    # Validate credentials
    if not validate_credentials(api_token):
        return 1

    # Request certificate
    logging.debug(f"Requesting certificate for {domain} with propagation wait: {propagation_seconds}s, staging: {staging} and email: {email}")
    return request_certificate(
        domain=domain,
        email=email,
        api_token=api_token,
        staging=staging,
        propagation_seconds=propagation_seconds,
    )


if __name__ == "__main__":
    sys.exit(main())
