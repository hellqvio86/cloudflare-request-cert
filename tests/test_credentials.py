from cloudflare_request_cert import main as c


def test_validate_credentials_missing(capsys):
    assert c.validate_credentials("") is False

    captured = capsys.readouterr()
    assert "CLOUDFLARE_API_TOKEN is required" in captured.err


def test_validate_credentials_ok():
    assert c.validate_credentials("abc123") is True


def test_validate_domain():
    assert c.validate_domain("example.com") is True
    assert c.validate_domain("sub.example.com") is True
    assert c.validate_domain("*.example.com") is True
    assert c.validate_domain("my-site.co.uk") is True

    # Argument injection / invalid domains
    assert c.validate_domain("--server=http://attacker.com") is False
    assert c.validate_domain("-d") is False
    assert c.validate_domain("") is False
    assert c.validate_domain(None) is False
    assert c.validate_domain("invalid domain with spaces.com") is False


def test_validate_email():
    assert c.validate_email("admin@example.com") is True
    assert c.validate_email("user.name+tag@sub.example.org") is True

    # Argument injection / invalid emails
    assert c.validate_email("--manual-auth-hook=/tmp/evil.sh") is False
    assert c.validate_email("-e") is False
    assert c.validate_email("") is False
    assert c.validate_email(None) is False
    assert c.validate_email("plainaddress") is False
    assert c.validate_email("@missingusername.com") is False
