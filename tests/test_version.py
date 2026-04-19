"""
Version compatibility tests
Tests: Server version check, API compatibility

Related to main project commit:
- feat: Multi-portfolio support requires version 0.2.0+
"""
import pytest
import re
from packaging import version


class TestVersionCompatibility:
    """Test server version compatibility"""

    def test_server_version_is_0_2_0_or_higher(self, api_client):
        """Server should be version 0.2.0 or higher for multi-portfolio support"""
        response = api_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data, "Response should contain version field"

        server_version = data["version"]
        assert isinstance(server_version, str), "Version should be a string"

        # Parse version string (handles versions like "0.2.0", "0.2.1", "0.3.0")
        try:
            parsed_version = version.parse(server_version)
            min_version = version.parse("0.2.0")
        except Exception as e:
            pytest.fail(f"Could not parse version '{server_version}': {e}")

        assert parsed_version >= min_version, (
            f"Server version {server_version} is too old. "
            f"Multi-portfolio tests require version 0.2.0 or higher. "
            f"Please upgrade portfolio-manager."
        )

    def test_version_format_is_semantic(self, api_client):
        """Version should follow semantic versioning format"""
        response = api_client.get("/")
        data = response.json()

        server_version = data["version"]
        # Basic semver pattern: major.minor.patch (e.g., 0.2.0)
        semver_pattern = r'^\d+\.\d+\.\d+([\-+].*)?$'
        assert re.match(semver_pattern, server_version), (
            f"Version '{server_version}' does not follow semantic versioning"
        )

    def test_health_endpoint_returns_version_info(self, api_client):
        """Health endpoint should indicate server is ready"""
        response = api_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "transactions_count" in data


@pytest.fixture(scope="session")
def require_v0_2_0(api_client):
    """
    Skip tests if server version is below 0.2.0.
    Use this fixture for multi-portfolio tests.
    """
    response = api_client.get("/")
    if response.status_code != 200:
        pytest.skip("Cannot determine server version - server unreachable")

    data = response.json()
    server_version = data.get("version", "0.0.0")

    try:
        parsed_version = version.parse(server_version)
        min_version = version.parse("0.2.0")
    except Exception:
        pytest.skip(f"Cannot parse server version: {server_version}")

    if parsed_version < min_version:
        pytest.skip(
            f"Server version {server_version} < 0.2.0. "
            f"Multi-portfolio feature not available."
        )
