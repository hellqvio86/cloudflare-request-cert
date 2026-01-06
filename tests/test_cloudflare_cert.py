"""Tests for cloudflare_cert module"""
import logging
import subprocess
from unittest.mock import MagicMock, patch

from cloudflare_cert import load_env_file, main, request_certificate, validate_credentials


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


class TestRequestCertificate:
    """Tests for request_certificate function"""

    @patch("cloudflare_cert.subprocess.run")
    @patch("cloudflare_cert.Path.mkdir")
    @patch("cloudflare_cert.Path.write_text")
    @patch("cloudflare_cert.Path.chmod")
    @patch("cloudflare_cert.Path.unlink")
    @patch("cloudflare_cert.Path.exists")
    def test_request_certificate_success(
        self, mock_exists, mock_unlink, mock_chmod, mock_write_text, mock_mkdir, mock_run, capsys
    ):
        """Test successful certificate request"""
        mock_run.return_value = MagicMock(returncode=0)
        mock_exists.return_value = True

        result = request_certificate(
            domain="example.com",
            email="admin@example.com",
            api_token="test_token",
            staging=False,
            propagation_seconds=10,
        )

        assert result == 0
        mock_run.assert_called_once()
        captured = capsys.readouterr()
        assert "Certificate successfully obtained" in captured.out

    @patch("cloudflare_cert.subprocess.run")
    @patch("cloudflare_cert.Path.mkdir")
    @patch("cloudflare_cert.Path.write_text")
    @patch("cloudflare_cert.Path.chmod")
    @patch("cloudflare_cert.Path.unlink")
    @patch("cloudflare_cert.Path.exists")
    def test_request_certificate_with_staging(
        self, mock_exists, mock_unlink, mock_chmod, mock_write_text, mock_mkdir, mock_run, capsys
    ):
        """Test certificate request with staging flag"""
        mock_run.return_value = MagicMock(returncode=0)
        mock_exists.return_value = True

        result = request_certificate(
            domain="example.com",
            email="admin@example.com",
            api_token="test_token",
            staging=True,
            propagation_seconds=10,
        )

        assert result == 0
        captured = capsys.readouterr()
        assert "STAGING" in captured.out

    @patch("cloudflare_cert.subprocess.run")
    @patch("cloudflare_cert.Path.mkdir")
    @patch("cloudflare_cert.Path.write_text")
    @patch("cloudflare_cert.Path.chmod")
    @patch("cloudflare_cert.Path.unlink")
    @patch("cloudflare_cert.Path.exists")
    def test_request_certificate_failure(
        self, mock_exists, mock_unlink, mock_chmod, mock_write_text, mock_mkdir, mock_run, capsys
    ):
        """Test failed certificate request"""
        mock_run.side_effect = subprocess.CalledProcessError(1, "certbot")
        mock_exists.return_value = True

        result = request_certificate(
            domain="example.com",
            email="admin@example.com",
            api_token="test_token",
            staging=False,
            propagation_seconds=10,
        )

        assert result == 1
        captured = capsys.readouterr()
        assert "Failed to obtain certificate" in captured.err

    @patch("cloudflare_cert.subprocess.run")
    @patch("cloudflare_cert.Path.mkdir")
    @patch("cloudflare_cert.Path.write_text")
    @patch("cloudflare_cert.Path.chmod")
    @patch("cloudflare_cert.Path.unlink")
    @patch("cloudflare_cert.Path.exists")
    def test_request_certificate_certbot_not_found(
        self, mock_exists, mock_unlink, mock_chmod, mock_write_text, mock_mkdir, mock_run, capsys
    ):
        """Test when certbot is not installed"""
        mock_run.side_effect = FileNotFoundError()
        mock_exists.return_value = False

        result = request_certificate(
            domain="example.com",
            email="admin@example.com",
            api_token="test_token",
            staging=False,
            propagation_seconds=10,
        )

        assert result == 1
        captured = capsys.readouterr()
        assert "certbot not found" in captured.err


class TestMain:
    """Tests for main function"""

    @patch("cloudflare_cert.request_certificate")
    @patch("cloudflare_cert.load_env_file")
    def test_main_with_cli_args(self, mock_load_env, mock_request_cert):
        """Test main with command-line arguments"""
        mock_load_env.return_value = {"CLOUDFLARE_API_TOKEN": "test_token"}
        mock_request_cert.return_value = 0

        with patch(
            "sys.argv", ["cloudflare_cert.py", "-d", "example.com", "-e", "admin@example.com"]
        ):
            result = main()

        assert result == 0
        mock_request_cert.assert_called_once()

    @patch("cloudflare_cert.load_env_file")
    def test_main_missing_domain(self, mock_load_env, capsys):
        """Test main with missing domain"""
        mock_load_env.return_value = {"CLOUDFLARE_API_TOKEN": "test_token"}

        with patch("sys.argv", ["cloudflare_cert.py", "-e", "admin@example.com"]):
            result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "DOMAIN is required" in captured.err

    @patch("cloudflare_cert.load_env_file")
    def test_main_missing_email(self, mock_load_env, capsys):
        """Test main with missing email"""
        mock_load_env.return_value = {"CLOUDFLARE_API_TOKEN": "test_token"}

        with patch("sys.argv", ["cloudflare_cert.py", "-d", "example.com"]):
            result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "EMAIL is required" in captured.err

    @patch("cloudflare_cert.load_env_file")
    def test_main_missing_api_token(self, mock_load_env, capsys):
        """Test main with missing API token"""
        mock_load_env.return_value = {}

        with patch(
            "sys.argv", ["cloudflare_cert.py", "-d", "example.com", "-e", "admin@example.com"]
        ):
            result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "CLOUDFLARE_API_TOKEN is required" in captured.err

    @patch("cloudflare_cert.request_certificate")
    @patch("cloudflare_cert.load_env_file")
    def test_main_with_env_file(self, mock_load_env, mock_request_cert):
        """Test main reading from .env file"""
        mock_load_env.return_value = {
            "CLOUDFLARE_API_TOKEN": "test_token",
            "DOMAIN": "example.com",
            "EMAIL": "admin@example.com",
        }
        mock_request_cert.return_value = 0

        with patch("sys.argv", ["cloudflare_cert.py"]):
            result = main()

        assert result == 0
        mock_request_cert.assert_called_once()

    @patch("cloudflare_cert.request_certificate")
    @patch("cloudflare_cert.load_env_file")
    def test_main_with_staging_flag(self, mock_load_env, mock_request_cert):
        """Test main with staging flag"""
        mock_load_env.return_value = {"CLOUDFLARE_API_TOKEN": "test_token"}
        mock_request_cert.return_value = 0

        with patch(
            "sys.argv",
            ["cloudflare_cert.py", "-d", "example.com", "-e", "admin@example.com", "--staging"],
        ):
            result = main()

        assert result == 0
        call_args = mock_request_cert.call_args
        assert call_args.kwargs["staging"] is True

    @patch("cloudflare_cert.request_certificate")
    @patch("cloudflare_cert.load_env_file")
    def test_main_with_custom_propagation(self, mock_load_env, mock_request_cert, caplog):
        """Test main with custom propagation seconds"""

        caplog.set_level(logging.DEBUG)

        mock_load_env.return_value = {"CLOUDFLARE_API_TOKEN": "test_token"}
        mock_request_cert.return_value = 0

        with patch(
            "sys.argv",
            [
                "cloudflare_cert.py",
                "-d",
                "example.com",
                "-e",
                "admin@example.com",
                "--propagation-seconds",
                "30",
            ],
        ):
            result = main()

        assert result == 0
        call_args = mock_request_cert.call_args
        assert call_args.kwargs["propagation_seconds"] == 30

    @patch("cloudflare_cert.request_certificate")
    @patch("cloudflare_cert.load_env_file")
    def test_main_env_staging_from_file(self, mock_load_env, mock_request_cert):
        """Test main with staging from env file"""
        mock_load_env.return_value = {"CLOUDFLARE_API_TOKEN": "test_token", "STAGING": "1"}
        mock_request_cert.return_value = 0

        with patch(
            "sys.argv", ["cloudflare_cert.py", "-d", "example.com", "-e", "admin@example.com"]
        ):
            result = main()

        assert result == 0
        call_args = mock_request_cert.call_args
        assert call_args.kwargs["staging"] is True
