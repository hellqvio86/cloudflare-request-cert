#!/usr/bin/env python3
"""
Cloudflare Request Cert - SSL/TLS certificate automation using Cloudflare DNS
"""

from __future__ import annotations

import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import TypedDict


class Config(TypedDict):
    domain: str | None
    email: str | None
    api_token: str | None
    staging: bool
    propagation_seconds: int


def load_env_file(env_file: Path) -> dict[str, str]:
    """Load environment variables from a .env file."""
    env_vars: dict[str, str] = {}
    if env_file.exists():
        with env_file.open() as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, _, value = line.partition("=")
                    env_vars[key.strip()] = value.strip().strip("\"'")
    logging.debug("Loaded environment variables: %s", env_vars)

    return env_vars


def load_config() -> Config:
    """
    Parse CLI args + env file + environment variables
    and return a merged config dictionary.
    """
    parser = argparse.ArgumentParser(
        description="Request SSL/TLS certificates using Cloudflare DNS"
    )
    parser.add_argument("-d", "--domain")
    parser.add_argument("-e", "--email")
    parser.add_argument("--staging", action="store_true")
    parser.add_argument("--propagation-seconds", type=int)
    parser.add_argument(
        "--env-file",
        type=Path,
        default=Path(".env"),
    )

    args = parser.parse_args()
    env_vars = load_env_file(args.env_file)

    config: Config = {
        "domain": args.domain or env_vars.get("DOMAIN") or os.getenv("DOMAIN"),
        "email": args.email or env_vars.get("EMAIL") or os.getenv("EMAIL"),
        "api_token": env_vars.get("CLOUDFLARE_API_TOKEN") or os.getenv("CLOUDFLARE_API_TOKEN"),
        "staging": (args.staging or env_vars.get("STAGING") == "1" or os.getenv("STAGING") == "1"),
        "propagation_seconds": (
            args.propagation_seconds or int(env_vars.get("PROPAGATION_SECONDS", "10"))
            if env_vars.get("PROPAGATION_SECONDS")
            else (args.propagation_seconds or 10)
        ),
    }

    return config


def validate_credentials(api_token: str | None) -> bool:
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
    credentials_dir = Path.home() / ".secrets" / "certbot"
    credentials_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    credentials_file = credentials_dir / "cloudflare.ini"

    credentials_file.write_text(f"dns_cloudflare_api_token = {api_token}\n")
    credentials_file.chmod(0o600)

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
        cmd.append("--staging")

    print(f"Requesting certificate for {domain}...")
    print(f"Using Cloudflare API (propagation wait: {propagation_seconds}s)")
    if staging:
        print("⚠️  Using STAGING environment (test certificates)")

    try:
        subprocess.run(cmd, check=True)
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
        if credentials_file.exists():
            credentials_file.unlink()


def main() -> int:
    config = load_config()

    if not config["domain"]:
        print("Error: DOMAIN is required", file=sys.stderr)
        return 1

    if not config["email"]:
        print("Error: EMAIL is required", file=sys.stderr)
        return 1

    if not validate_credentials(config["api_token"]):
        return 1

    logging.debug(
        "Requesting certificate for %s with propagation=%ss staging=%s email=%s",
        config["domain"],
        config["propagation_seconds"],
        config["staging"],
        config["email"],
    )

    return request_certificate(
        domain=config["domain"],
        email=config["email"],
        api_token=config["api_token"],  # type: ignore[arg-type]
        staging=config["staging"],
        propagation_seconds=config["propagation_seconds"],
    )


if __name__ == "__main__":
    sys.exit(main())
