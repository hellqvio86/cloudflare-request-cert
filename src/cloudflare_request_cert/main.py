#!/usr/bin/env python3
"""
Cloudflare Request Cert - SSL/TLS certificate automation using Cloudflare DNS
"""

from __future__ import annotations

import argparse
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import TypedDict

DOMAIN_PATTERN = re.compile(
    r"^(\*\.)?([a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,63}$"
)
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
SENSITIVE_KEYWORDS = ("TOKEN", "SECRET", "KEY", "PASS", "AUTH", "CREDENTIAL")


class Config(TypedDict):
    domain: str | None
    email: str | None
    api_token: str | None
    staging: bool
    propagation_seconds: int


def _redact_env(env_vars: dict[str, str]) -> dict[str, str]:
    """Return a copy of env_vars with sensitive values redacted."""
    return {
        k: ("***" if any(kw in k.upper() for kw in SENSITIVE_KEYWORDS) else v)
        for k, v in env_vars.items()
    }


def load_env_file(env_file: Path) -> dict[str, str]:
    """Load environment variables from a .env file."""
    env_vars: dict[str, str] = {}
    if env_file.exists():
        with env_file.open() as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    logging.warning("Ignoring malformed line in .env file (missing '='): %s", line)
                    continue
                key, _, value = line.partition("=")
                env_vars[key.strip()] = value.strip().strip("\"'")
    logging.debug("Loaded environment variables: %s", _redact_env(env_vars))

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

    raw_propagation = env_vars.get("PROPAGATION_SECONDS") or os.getenv("PROPAGATION_SECONDS")
    propagation_seconds = args.propagation_seconds
    if propagation_seconds is None and raw_propagation is not None:
        try:
            propagation_seconds = int(raw_propagation)
        except ValueError:
            print(
                f"Error: Invalid PROPAGATION_SECONDS value: '{raw_propagation}' "
                "(must be a positive integer)",
                file=sys.stderr,
            )
            propagation_seconds = -1
    if propagation_seconds is None:
        propagation_seconds = 10

    config: Config = {
        "domain": args.domain or env_vars.get("DOMAIN") or os.getenv("DOMAIN"),
        "email": args.email or env_vars.get("EMAIL") or os.getenv("EMAIL"),
        "api_token": env_vars.get("CLOUDFLARE_API_TOKEN") or os.getenv("CLOUDFLARE_API_TOKEN"),
        "staging": (args.staging or env_vars.get("STAGING") == "1" or os.getenv("STAGING") == "1"),
        "propagation_seconds": propagation_seconds,
    }

    return config


def validate_domain(domain: str | None) -> bool:
    """Validate domain name format and reject argument injection attempts."""
    if not domain:
        print("Error: DOMAIN is required", file=sys.stderr)
        return False
    if domain.startswith("-") or not DOMAIN_PATTERN.match(domain):
        print(f"Error: Invalid domain format: '{domain}'", file=sys.stderr)
        return False
    return True


def validate_email(email: str | None) -> bool:
    """Validate email address format and reject argument injection attempts."""
    if not email:
        print("Error: EMAIL is required", file=sys.stderr)
        return False
    if email.startswith("-") or not EMAIL_PATTERN.match(email):
        print(f"Error: Invalid email format: '{email}'", file=sys.stderr)
        return False
    return True


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
    if not validate_domain(domain):
        return 1
    if not validate_email(email):
        return 1
    if propagation_seconds <= 0:
        print(
            f"Error: Propagation seconds must be positive, got {propagation_seconds}",
            file=sys.stderr,
        )
        return 1

    credentials_dir = Path.home() / ".secrets" / "certbot"
    credentials_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        credentials_dir.chmod(0o700)
    except OSError:
        pass

    credentials_file: Path | None = None
    try:
        fd, temp_path = tempfile.mkstemp(
            dir=credentials_dir,
            prefix="cloudflare-",
            suffix=".ini",
        )
        credentials_file = Path(temp_path)
        with os.fdopen(fd, "w") as f:
            f.write(f"dns_cloudflare_api_token = {api_token}\n")

        # Detect certbot path (checks venv bin first, then system PATH)
        python_bin_dir = Path(sys.executable).parent
        venv_certbot = python_bin_dir / "certbot"
        if venv_certbot.exists() and os.access(venv_certbot, os.X_OK):
            certbot_path = str(venv_certbot)
        else:
            certbot_path = shutil.which("certbot") or "certbot"

        cmd = [
            certbot_path,
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
        if credentials_file and credentials_file.exists():
            try:
                credentials_file.unlink()
            except OSError:
                pass


def main() -> int:
    config = load_config()

    if not validate_domain(config["domain"]):
        return 1

    if not validate_email(config["email"]):
        return 1

    if not validate_credentials(config["api_token"]):
        return 1

    if config["propagation_seconds"] <= 0:
        print("Error: PROPAGATION_SECONDS must be a positive integer", file=sys.stderr)
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
