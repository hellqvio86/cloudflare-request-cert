import logging
import textwrap
from pathlib import Path

from cloudflare_request_cert import main as c


def test_load_env_file(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text(
        textwrap.dedent("""
        # comment
        DOMAIN=example.com
        EMAIL=admin@example.com
        CLOUDFLARE_API_TOKEN=abc123
        PROPAGATION_SECONDS=20
        malformed line without equal sign
    """)
    )

    result = c.load_env_file(env)

    assert result["DOMAIN"] == "example.com"
    assert result["EMAIL"] == "admin@example.com"
    assert result["CLOUDFLARE_API_TOKEN"] == "abc123"
    assert result["PROPAGATION_SECONDS"] == "20"
    assert "malformed line without equal sign" not in result


def test_load_env_file_redaction(tmp_path: Path, caplog):
    env = tmp_path / ".env"
    env.write_text(
        textwrap.dedent("""
        CLOUDFLARE_API_TOKEN=super_secret_token
        API_KEY=my_key
        DOMAIN=example.com
    """)
    )

    with caplog.at_level(logging.DEBUG):
        c.load_env_file(env)

    assert "super_secret_token" not in caplog.text
    assert "my_key" not in caplog.text
    assert "***" in caplog.text


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


def test_load_config_invalid_propagation(monkeypatch, tmp_path, capsys):
    env = tmp_path / ".env"
    env.write_text("PROPAGATION_SECONDS=invalid_number\n")

    monkeypatch.setattr("sys.argv", ["prog", "--env-file", str(env)])

    config = c.load_config()
    captured = capsys.readouterr()

    assert config["propagation_seconds"] == -1
    assert "Invalid PROPAGATION_SECONDS value" in captured.err
