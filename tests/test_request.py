import stat
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

from cloudflare_request_cert import main as c


def test_request_certificate_success(tmp_path, monkeypatch):
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

    captured_cmd = []

    def fake_run(cmd, check=True):
        captured_cmd.extend(cmd)
        # Verify credentials file exists during execution and has 0600 mode
        cred_file_arg = cmd[cmd.index("--dns-cloudflare-credentials") + 1]
        p = Path(cred_file_arg)
        assert p.exists()
        # Verify file mode is 0600 (read/write only by owner)
        file_mode = stat.S_IMODE(p.stat().st_mode)
        assert file_mode == 0o600
        # Verify directory mode is 0700
        dir_mode = stat.S_IMODE(p.parent.stat().st_mode)
        assert dir_mode == 0o700
        return MagicMock(returncode=0)

    with patch("subprocess.run", side_effect=fake_run) as mock_run:
        rc = c.request_certificate(
            domain="example.com",
            email="admin@example.com",
            api_token="abc123",
            staging=False,
            propagation_seconds=5,
        )

    assert rc == 0
    mock_run.assert_called_once()
    # Check that any temporary credentials files were removed
    certbot_dir = tmp_path / ".secrets" / "certbot"
    assert list(certbot_dir.glob("cloudflare-*.ini")) == []


def test_request_certificate_staging_flag(tmp_path, monkeypatch):
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

    captured_cmd = []

    def fake_run(cmd, check=True):
        captured_cmd.extend(cmd)
        return MagicMock(returncode=0)

    with patch("subprocess.run", side_effect=fake_run):
        rc = c.request_certificate(
            domain="*.example.com",
            email="admin@example.com",
            api_token="abc123",
            staging=True,
            propagation_seconds=15,
        )

    assert rc == 0
    assert "--staging" in captured_cmd
    assert "-d" in captured_cmd
    assert "*.example.com" in captured_cmd
    assert "--dns-cloudflare-propagation-seconds" in captured_cmd
    assert "15" in captured_cmd


def test_request_certificate_subprocess_failure(tmp_path, monkeypatch):
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

    with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "cmd")):
        rc = c.request_certificate(
            domain="example.com",
            email="admin@example.com",
            api_token="abc123",
            staging=False,
            propagation_seconds=5,
        )

    assert rc == 1
    # Check cleanup even on failure
    certbot_dir = tmp_path / ".secrets" / "certbot"
    assert list(certbot_dir.glob("cloudflare-*.ini")) == []


def test_request_certificate_filenotfound(tmp_path, monkeypatch):
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

    with patch("subprocess.run", side_effect=FileNotFoundError):
        rc = c.request_certificate(
            domain="example.com",
            email="admin@example.com",
            api_token="abc123",
        )

    assert rc == 1
    certbot_dir = tmp_path / ".secrets" / "certbot"
    assert list(certbot_dir.glob("cloudflare-*.ini")) == []


def test_request_certificate_invalid_args():
    assert (
        c.request_certificate(
            domain="--server=attacker.com",
            email="admin@example.com",
            api_token="abc123",
        )
        == 1
    )
    assert (
        c.request_certificate(
            domain="example.com",
            email="--hook=evil.sh",
            api_token="abc123",
        )
        == 1
    )
    assert (
        c.request_certificate(
            domain="example.com",
            email="admin@example.com",
            api_token="abc123",
            propagation_seconds=0,
        )
        == 1
    )
