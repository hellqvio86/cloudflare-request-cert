# Cloudflare Request Cert
![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![PyPI](https://img.shields.io/pypi/v/cloudflare-request-cert)
![Build](https://github.com/hellqvio86/cloudflare-request-cert/actions/workflows/ci.yml/badge.svg)
![Coverage](https://img.shields.io/badge/coverage-80%25%2B-green)
![License](https://img.shields.io/github/license/hellqvio86/cloudflare-request-cert)

A Python tool for requesting and renewing SSL/TLS certificates using Cloudflare DNS API with Let's Encrypt. Built with modern Python tooling using [uv](https://github.com/astral-sh/uv) for fast dependency management.

## Features

- 🔒 Automated SSL/TLS certificate requests using DNS-01 challenge
- ☁️ Cloudflare DNS API integration
- ⚡ Fast dependency management with uv
- 🛠️ Simple Makefile interface
- 🔄 Support for certificate renewal
- 🧪 Staging environment support for testing
- 📝 Configuration via .env file or command-line arguments
- 🔧 Flexible: use .env, CLI args, or both

## Prerequisites

- Python 3.10 or higher
- A Cloudflare account with API token
- Domain managed by Cloudflare DNS

## Installation

### Quick Setup

```bash
# Install dependencies (will install uv if not present)
make install
```

### Manual uv Installation

If you prefer to install uv manually:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Configuration

### 1. Get Cloudflare API Token

1. Log in to your [Cloudflare dashboard](https://dash.cloudflare.com/)
2. Go to **My Profile** → **API Tokens**
3. Create a token with these permissions:
   - **Zone:DNS:Edit** for the zones you want to manage
   - **Zone:Zone:Read** for all zones

### 2. Set Up Credentials

Create a `.env` file in the project root:

```bash
# Copy the example file
cp .env.example .env

# Edit with your credentials
nano .env
```

Your `.env` file can contain:

```bash
# Required
CLOUDFLARE_API_TOKEN=your_cloudflare_api_token_here

# Optional (can also be passed as CLI arguments)
DOMAIN=example.com
EMAIL=admin@example.com

# Optional settings
STAGING=0                    # Set to 1 for staging/test certificates
PROPAGATION_SECONDS=10       # DNS propagation wait time
```

**Security Note**: The `.env` file is already in `.gitignore`. Never commit API tokens to version control.

## Usage

### Three Ways to Use This Tool

#### 1. Using .env File Only

Set everything in `.env` and run without arguments:

```bash
# .env file contains: CLOUDFLARE_API_TOKEN, DOMAIN, EMAIL
uv run python cloudflare_cert.py
```

#### 2. Using Command-Line Arguments Only

```bash
# Provide all parameters via CLI (API token still from .env or environment)
uv run python cloudflare_cert.py -d example.com -e admin@example.com
```

#### 3. Mix of Both (Recommended)

```bash
# Store sensitive data in .env, pass domain/email via CLI
# This is useful when managing multiple domains
uv run python cloudflare_cert.py -d example.com -e admin@example.com
```

### Using Make Commands

Request a certificate with Make:

```bash
# Basic usage
make run DOMAIN=example.com EMAIL=admin@example.com

# Test with staging first (recommended)
make run DOMAIN=example.com EMAIL=admin@example.com STAGING=1
```

### Advanced Options

```bash
# Custom DNS propagation time
uv run python cloudflare_cert.py \
  -d example.com \
  -e admin@example.com \
  --propagation-seconds 30

# Use staging environment for testing
uv run python cloudflare_cert.py \
  -d example.com \
  -e admin@example.com \
  --staging

# Use custom .env file
uv run python cloudflare_cert.py \
  -d example.com \
  -e admin@example.com \
  --env-file /path/to/custom.env
```

### Priority Order

When the same setting is provided in multiple places, this is the priority order (highest to lowest):

1. **Command-line arguments** (highest priority)
2. **.env file**
3. **Environment variables** (lowest priority)

Example:
```bash
# .env has DOMAIN=old.com
# This will use new.com (CLI argument takes precedence)
uv run python cloudflare_cert.py -d new.com -e admin@example.com
```

## Makefile Commands

| Command        | Description                                       |
| -------------- | ------------------------------------------------- |
| `make help`    | Show all available commands                       |
| `make venv`    | Create virtual environment                        |
| `make install` | Install uv and sync dependencies (alias for venv) |
| `make sync`    | Sync dependencies with uv                         |
| `make dev`     | Install development dependencies                  |
| `make run`     | Run the certificate request tool                  |
| `make lint`    | Lint code with ruff                               |
| `make format`  | Format code with ruff                             |
| `make check`   | Run all checks (lint + format)                    |
| `make test`    | Run tests                                         |
| `make sbom`    | Generate SBOM (Software Bill of Materials)        |
| `make clean`   | Remove virtual environment and cache              |

## Certificate Locations

After successful certificate generation, your certificates will be stored at:

```
/etc/letsencrypt/live/your-domain.com/
├── cert.pem       # Your certificate
├── chain.pem      # The certificate chain
├── fullchain.pem  # cert.pem + chain.pem
└── privkey.pem    # Your private key
```

## DNS Propagation Time

The tool waits for DNS changes to propagate before Let's Encrypt validates your domain. Default is 10 seconds, but you can adjust this:

```bash
# Via CLI
python cloudflare_cert.py -d example.com -e admin@example.com --propagation-seconds 30

# Via .env
PROPAGATION_SECONDS=30
```

## Automatic Renewal

Certbot automatically handles renewal. Set up a cron job or systemd timer:

```bash
# Cron example (runs daily at 2 AM)
0 2 * * * certbot renew --quiet

# Or use systemd timer (recommended)
sudo systemctl enable --now certbot-renew.timer
```

## Development

### Install Development Dependencies

```bash
make dev
```

### Run Tests

```bash
make test
```

### Run Linting

```bash
make lint
```

### Format Code

```bash
make format
```

### Run All Checks

```bash
make check
```

### Generate SBOM
Generate a Software Bill of Materials (SBOM) in CycloneDX JSON format:
```bash
make sbom
```
The SBOM will be saved to `bom.json`.

## Example Workflows

### First Time Setup

```bash
# 1. Install dependencies
make install

# 2. Set up configuration
cp .env.example .env
nano .env  # Add your Cloudflare API token

# 3. Test with staging (won't affect rate limits)
uv run python cloudflare_cert.py -d example.com -e admin@example.com --staging

# 4. Get production certificate
uv run python cloudflare_cert.py -d example.com -e admin@example.com
```

### Managing Multiple Domains

```bash
# Store API token in .env
echo "CLOUDFLARE_API_TOKEN=your_token" > .env

# Request certificates for different domains
uv run python cloudflare_cert.py -d site1.com -e admin@site1.com
uv run python cloudflare_cert.py -d site2.com -e admin@site2.com
uv run python cloudflare_cert.py -d site3.com -e admin@site3.com
```

### Automated Script

```bash
#!/bin/bash
# renew-certs.sh

DOMAINS=("site1.com" "site2.com" "site3.com")
EMAIL="admin@example.com"

for domain in "${DOMAINS[@]}"; do
    echo "Requesting certificate for $domain..."
    uv run python cloudflare_cert.py -d "$domain" -e "$EMAIL"
done
```

## Troubleshooting

### "certbot not found"

Install certbot and the Cloudflare plugin:

```bash
make install
# or
uv sync
```

### "CLOUDFLARE_API_TOKEN is required"

Make sure your `.env` file exists and contains:
```bash
CLOUDFLARE_API_TOKEN=your_actual_token_here
```

### "DOMAIN is required" or "EMAIL is required"

Either set them in `.env`:
```bash
DOMAIN=example.com
EMAIL=admin@example.com
```

Or pass them as arguments:
```bash
uv run python cloudflare_cert.py -d example.com -e admin@example.com
```

### API Token Permissions

Ensure your Cloudflare API token has:
- Zone:DNS:Edit permissions
- Zone:Zone:Read permissions

### DNS Propagation Issues

If validation fails, try increasing propagation time:

```bash
uv run python cloudflare_cert.py -d example.com -e admin@example.com --propagation-seconds 60
```

Or set in `.env`:
```bash
PROPAGATION_SECONDS=60
```

### Rate Limits

Let's Encrypt has rate limits. Use staging for testing:

```bash
# Set in .env
STAGING=1

# Or via CLI
uv run python cloudflare_cert.py -d example.com -e admin@example.com --staging
```

## Comparison with Original

This is a Cloudflare remake of the [loopia-request-cert](https://github.com/hellqvio86/loopia-request-cert) tool with several improvements:

- Uses **Cloudflare** instead of Loopia DNS
- Uses **uv** for faster dependency management (10-100x faster than pip)
- Modern **pyproject.toml** configuration
- Improved **Makefile** with more commands
- Better **error handling** and user feedback
- **Flexible configuration**: .env file, CLI args, or both
- **Type hints** for better code quality
- **Ruff** for linting and formatting
- **Comprehensive tests**

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Resources

- [Cloudflare API Documentation](https://developers.cloudflare.com/api/)
- [Certbot Documentation](https://eff-certbot.readthedocs.io/)
- [Let's Encrypt](https://letsencrypt.org/)
- [uv Documentation](https://github.com/astral-sh/uv)
