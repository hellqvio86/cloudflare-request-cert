"""Tests for cloudflare_cert module"""

from cloudflare_cert import load_env_file, validate_credentials


class TestLoadEnvFile:
    """Tests for load_env_file function"""

    def test_load_env_file_with_valid_content(self, tmp_path):
        """Test loading a valid .env file"""
        env_file = tmp_path / ".env"
        env_file.write_text("CLOUDFLARE_API_TOKEN=test_token_123\n")

        result = load_env_file(env_file)

        assert result == {"CLOUDFLARE_API_TOKEN": "test_token_123"}

    def test_load_env_file_with_quotes(self, tmp_path):
        """Test loading env file with quoted values"""
        env_file = tmp_path / ".env"
        env_file.write_text('CLOUDFLARE_API_TOKEN="test_token_123"\n')

        result = load_env_file(env_file)

        assert result == {"CLOUDFLARE_API_TOKEN": "test_token_123"}

    def test_load_env_file_ignores_comments(self, tmp_path):
        """Test that comments are ignored"""
        env_file = tmp_path / ".env"
        env_file.write_text("# This is a comment\nCLOUDFLARE_API_TOKEN=test_token\n")

        result = load_env_file(env_file)

        assert result == {"CLOUDFLARE_API_TOKEN": "test_token"}

    def test_load_env_file_nonexistent(self, tmp_path):
        """Test loading non-existent file returns empty dict"""
        env_file = tmp_path / "nonexistent.env"

        result = load_env_file(env_file)

        assert result == {}

    def test_load_env_file_multiple_values(self, tmp_path):
        """Test loading multiple environment variables"""
        env_file = tmp_path / ".env"
        env_file.write_text("VAR1=value1\nVAR2=value2\n")

        result = load_env_file(env_file)

        assert result == {"VAR1": "value1", "VAR2": "value2"}

    def test_load_env_file_with_domain_and_email(self, tmp_path):
        """Test loading DOMAIN and EMAIL from env file"""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "CLOUDFLARE_API_TOKEN=token123\nDOMAIN=example.com\nEMAIL=admin@example.com\n"
        )

        result = load_env_file(env_file)

        assert result == {
            "CLOUDFLARE_API_TOKEN": "token123",
            "DOMAIN": "example.com",
            "EMAIL": "admin@example.com",
        }

    def test_load_env_file_with_staging_flag(self, tmp_path):
        """Test loading STAGING flag from env file"""
        env_file = tmp_path / ".env"
        env_file.write_text("STAGING=1\n")

        result = load_env_file(env_file)

        assert result == {"STAGING": "1"}

    def test_load_env_file_with_propagation_seconds(self, tmp_path):
        """Test loading PROPAGATION_SECONDS from env file"""
        env_file = tmp_path / ".env"
        env_file.write_text("PROPAGATION_SECONDS=30\n")

        result = load_env_file(env_file)

        assert result == {"PROPAGATION_SECONDS": "30"}


class TestValidateCredentials:
    """Tests for validate_credentials function"""

    def test_validate_credentials_with_token(self):
        """Test validation with valid token"""
        assert validate_credentials("valid_token") is True

    def test_validate_credentials_without_token(self, capsys):
        """Test validation without token"""
        result = validate_credentials(None)
        captured = capsys.readouterr()

        assert result is False
        assert "CLOUDFLARE_API_TOKEN is required" in captured.err

    def test_validate_credentials_empty_string(self, capsys):
        """Test validation with empty string"""
        result = validate_credentials("")
        captured = capsys.readouterr()

        assert result is False
        assert "CLOUDFLARE_API_TOKEN is required" in captured.err
