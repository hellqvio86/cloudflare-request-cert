import cloudflare_request_cert as c


def test_validate_credentials_missing(capsys):
    assert c.validate_credentials("") is False

    captured = capsys.readouterr()
    assert "CLOUDFLARE_API_TOKEN is required" in captured.err


def test_validate_credentials_ok():
    assert c.validate_credentials("abc123") is True
