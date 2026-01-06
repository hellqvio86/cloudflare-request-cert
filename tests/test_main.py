import cloudflare_request_cert as c


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
