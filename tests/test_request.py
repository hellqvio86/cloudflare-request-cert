from pathlib import Path
import subprocess
import cloudflare_request_cert as c


def test_request_certificate_success(mocker, tmp_path, monkeypatch):
    mock_run = mocker.patch("subprocess.run")

    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

    rc = c.request_certificate(
        domain="example.com",
        email="admin@example.com",
        api_token="abc123",
        staging=False,
        propagation_seconds=5,
    )

    assert rc == 0
    mock_run.assert_called_once()
    assert (tmp_path / ".secrets" / "certbot" / "cloudflare.ini").exists() is False


def test_request_certificate_subprocess_failure(mocker, tmp_path, monkeypatch):
    mocker.patch(
        "subprocess.run",
        side_effect=subprocess.CalledProcessError(1, "cmd")
    )

    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

    rc = c.request_certificate(
        domain="example.com",
        email="admin@example.com",
        api_token="abc123",
        staging=False,
        propagation_seconds=5,
    )

    assert rc == 1
