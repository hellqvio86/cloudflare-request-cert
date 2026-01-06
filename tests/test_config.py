import textwrap
from pathlib import Path

import cloudflare_cert as c


def test_load_env_file(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text(
        textwrap.dedent("""
        # comment
        DOMAIN=example.com
        EMAIL=admin@example.com
        CLOUDFLARE_API_TOKEN=abc123
        PROPAGATION_SECONDS=20
    """)
    )

    result = c.load_env_file(env)

    assert result["DOMAIN"] == "example.com"
    assert result["EMAIL"] == "admin@example.com"
    assert result["CLOUDFLARE_API_TOKEN"] == "abc123"
    assert result["PROPAGATION_SECONDS"] == "20"


def test_load_config_success(monkeypatch, tmp_path):
    env = tmp_path / ".env"
    env.write_text("CLOUDFLARE_API_TOKEN=abc123\n")

    monkeypatch.setenv("DOMAIN", "example.com")
    monkeypatch.setenv("EMAIL", "admin@example.com")

    monkeypatch.setattr("sys.argv", ["prog", "--env-file", str(env)])

    config = c.load_config()

    assert config["domain"] == "example.com"
    assert config["email"] == "admin@example.com"
    assert config["api_token"] == "abc123"
    assert config["propagation_seconds"] == 10
    assert config["staging"] is False
