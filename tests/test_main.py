from cloudflare_request_cert import main as c


def test_main_success(monkeypatch):
    monkeypatch.setattr(
        c,
        "load_config",
        lambda: {
            "domain": "example.com",
            "email": "admin@example.com",
            "api_token": "abc123",
            "staging": False,
            "propagation_seconds": 10,
        },
    )

    monkeypatch.setattr(c, "validate_credentials", lambda token: True)
    monkeypatch.setattr(c, "request_certificate", lambda **kwargs: 0)

    assert c.main() == 0


def test_main_failure(monkeypatch):
    monkeypatch.setattr(
        c,
        "load_config",
        lambda: {
            "domain": "example.com",
            "email": "admin@example.com",
            "api_token": "abc123",
            "staging": False,
            "propagation_seconds": 10,
        },
    )

    monkeypatch.setattr(c, "validate_credentials", lambda token: False)

    assert c.main() == 1


def test_main_invalid_domain(monkeypatch):
    monkeypatch.setattr(
        c,
        "load_config",
        lambda: {
            "domain": "--attacker-flag",
            "email": "admin@example.com",
            "api_token": "abc123",
            "staging": False,
            "propagation_seconds": 10,
        },
    )

    assert c.main() == 1


def test_main_invalid_email(monkeypatch):
    monkeypatch.setattr(
        c,
        "load_config",
        lambda: {
            "domain": "example.com",
            "email": "--evil-hook",
            "api_token": "abc123",
            "staging": False,
            "propagation_seconds": 10,
        },
    )

    assert c.main() == 1


def test_main_invalid_propagation(monkeypatch):
    monkeypatch.setattr(
        c,
        "load_config",
        lambda: {
            "domain": "example.com",
            "email": "admin@example.com",
            "api_token": "abc123",
            "staging": False,
            "propagation_seconds": -1,
        },
    )

    assert c.main() == 1
