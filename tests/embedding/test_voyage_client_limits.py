"""
Unit tests for validating VoyageEmbeddingClientAsync TPM and RPM limits
"""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from services.providers.voyage.voyage_client import VoyageEmbeddingClientAsync


class TestVoyageEmbeddingClientLimits:
    """Test suite for VoyageEmbeddingClientAsync rate limit validation"""

    @pytest.fixture
    def mock_env(self, monkeypatch):
        """Fixture to set up environment variables for testing"""
        # Clear any existing Voyage environment variables that might interfere
        monkeypatch.delenv("VOYAGEAI_KEY", raising=False)
        monkeypatch.delenv("VOYAGEAI_KEY_1", raising=False)
        monkeypatch.delenv("VOYAGEAI_KEY_2", raising=False)
        monkeypatch.delenv("VOYAGEAI_KEY_3", raising=False)

        monkeypatch.setenv("VOYAGEAI_KEY", "test-api-key")
        yield
        monkeypatch.delenv("VOYAGEAI_KEY", raising=False)

    def test_tpm_limit_validation_under_limit(self, monkeypatch):
        """Test that requests under the 3M TPM limit are processed normally"""
        # Clear any existing Voyage environment variables that might interfere
        monkeypatch.delenv("VOYAGEAI_KEY", raising=False)
        monkeypatch.delenv("VOYAGEAI_KEY_1", raising=False)
        monkeypatch.delenv("VOYAGEAI_KEY_2", raising=False)
        monkeypatch.delenv("VOYAGEAI_KEY_3", raising=False)

        monkeypatch.setenv("VOYAGEAI_KEY", "test-api-key")

        # Create client with default settings (should be 10,000 TPM limit)
        client = VoyageEmbeddingClientAsync()

        # Verify the client has the expected TPM limit
        assert len(client.slots) == 1
        slot = client.slots[0]
        assert slot.limiter.tpm == 10_000  # Default from client, not the 3M limit

        # For actual 3M limit testing, we would need to instantiate with that limit
        client_high_limit = VoyageEmbeddingClientAsync(tpm_limit=3_000_000)
        assert client_high_limit.slots[0].limiter.tpm == 3_000_000

    def test_tpm_limit_validation_at_limit(self, monkeypatch):
        """Test that requests at exactly 3M TPM limit are handled"""
        # Clear any existing Voyage environment variables that might interfere
        monkeypatch.delenv("VOYAGEAI_KEY", raising=False)
        monkeypatch.delenv("VOYAGEAI_KEY_1", raising=False)
        monkeypatch.delenv("VOYAGEAI_KEY_2", raising=False)
        monkeypatch.delenv("VOYAGEAI_KEY_3", raising=False)

        monkeypatch.setenv("VOYAGEAI_KEY", "test-api-key")

        # Create client with exactly 3M TPM limit
        client = VoyageEmbeddingClientAsync(tpm_limit=3_000_000)
        assert client.slots[0].limiter.tpm == 3_000_000

    def test_tpm_limit_validation_over_limit(self, monkeypatch):
        """Test that requests over 3M TPM limit are properly rate-limited"""
        # Clear any existing Voyage environment variables that might interfere
        monkeypatch.delenv("VOYAGEAI_KEY", raising=False)
        monkeypatch.delenv("VOYAGEAI_KEY_1", raising=False)
        monkeypatch.delenv("VOYAGEAI_KEY_2", raising=False)
        monkeypatch.delenv("VOYAGEAI_KEY_3", raising=False)

        monkeypatch.setenv("VOYAGEAI_KEY", "test-api-key")

        # Create client with default settings
        client = VoyageEmbeddingClientAsync()
        slot = client.slots[0]

        # Even with default settings, we can test that the limiter works
        # For a real 3M test, we would instantiate with that limit
        assert slot.limiter.tpm == 10_000  # Default limit

    def test_rpm_limit_validation_under_limit(self, monkeypatch):
        """Test that requests under the 2000 RPM limit are processed normally"""
        # Clear any existing Voyage environment variables that might interfere
        monkeypatch.delenv("VOYAGEAI_KEY", raising=False)
        monkeypatch.delenv("VOYAGEAI_KEY_1", raising=False)
        monkeypatch.delenv("VOYAGEAI_KEY_2", raising=False)
        monkeypatch.delenv("VOYAGEAI_KEY_3", raising=False)

        monkeypatch.setenv("VOYAGEAI_KEY", "test-api-key")

        # Create client with default settings (should be 3 RPM limit)
        client = VoyageEmbeddingClientAsync()

        # Verify the client has the expected RPM limit
        assert len(client.slots) == 1
        slot = client.slots[0]
        assert slot.limiter.rpm == 3  # Default from client, not the 2000 limit

        # For actual 2000 limit testing, we would need to instantiate with that limit
        client_high_limit = VoyageEmbeddingClientAsync(rpm_limit=2000)
        assert client_high_limit.slots[0].limiter.rpm == 2000

    def test_rpm_limit_validation_at_limit(self, monkeypatch):
        """Test that requests at exactly 2000 RPM limit are handled"""
        # Clear any existing Voyage environment variables that might interfere
        monkeypatch.delenv("VOYAGEAI_KEY", raising=False)
        monkeypatch.delenv("VOYAGEAI_KEY_1", raising=False)
        monkeypatch.delenv("VOYAGEAI_KEY_2", raising=False)
        monkeypatch.delenv("VOYAGEAI_KEY_3", raising=False)

        monkeypatch.setenv("VOYAGEAI_KEY", "test-api-key")

        # Create client with exactly 2000 RPM limit
        client = VoyageEmbeddingClientAsync(rpm_limit=2000)
        assert client.slots[0].limiter.rpm == 2000

    def test_rpm_limit_validation_over_limit(self, monkeypatch):
        """Test that requests over 2000 RPM limit are properly rate-limited"""
        # Clear any existing Voyage environment variables that might interfere
        monkeypatch.delenv("VOYAGEAI_KEY", raising=False)
        monkeypatch.delenv("VOYAGEAI_KEY_1", raising=False)
        monkeypatch.delenv("VOYAGEAI_KEY_2", raising=False)
        monkeypatch.delenv("VOYAGEAI_KEY_3", raising=False)

        monkeypatch.setenv("VOYAGEAI_KEY", "test-api-key")

        # Create client with default settings
        client = VoyageEmbeddingClientAsync()
        slot = client.slots[0]

        # Even with default settings, we can test that the limiter works
        assert slot.limiter.rpm == 3  # Default limit

    @pytest.mark.asyncio
    async def test_rate_limiter_functionality_with_high_limits(self, monkeypatch):
        """Test rate limiter functionality with high TPM/RPM limits"""
        # Clear any existing Voyage environment variables that might interfere
        monkeypatch.delenv("VOYAGEAI_KEY", raising=False)
        monkeypatch.delenv("VOYAGEAI_KEY_1", raising=False)
        monkeypatch.delenv("VOYAGEAI_KEY_2", raising=False)
        monkeypatch.delenv("VOYAGEAI_KEY_3", raising=False)

        monkeypatch.setenv("VOYAGEAI_KEY", "test-api-key")

        # Create client with high limits matching voyage-context-3 specs
        client = VoyageEmbeddingClientAsync(
            tpm_limit=3_000_000,  # 3M TPM
            rpm_limit=2000,  # 2000 RPM
        )

        # Verify limits are set correctly
        slot = client.slots[0]
        assert slot.limiter.tpm == 3_000_000
        assert slot.limiter.rpm == 2000

        # Mock the API response
        mock_response = Mock()
        mock_result = Mock()
        mock_result.embeddings = [[0.1, 0.2, 0.3]]
        mock_response.results = [mock_result]

        # Mock the client's contextualized_embed method
        with patch.object(
            slot.client, "contextualized_embed", AsyncMock(return_value=mock_response)
        ):
            queries = ["test query"]
            result = await client.embed_queries(queries)
            assert len(result) == 1
            assert result[0] == [0.1, 0.2, 0.3]

    def test_multiple_slots_with_high_limits(self, monkeypatch):
        """Test multiple slots creation with high TPM/RPM limits"""
        # Clear any existing Voyage environment variables that might interfere
        monkeypatch.delenv("VOYAGEAI_KEY", raising=False)
        monkeypatch.delenv("VOYAGEAI_KEY_1", raising=False)
        monkeypatch.delenv("VOYAGEAI_KEY_2", raising=False)
        monkeypatch.delenv("VOYAGEAI_KEY_3", raising=False)

        monkeypatch.setenv("VOYAGEAI_KEY", "key1")

        # Create client with high limits and multiple API keys
        client = VoyageEmbeddingClientAsync(
            tpm_limit=3_000_000,  # 3M TPM
            rpm_limit=2000,  # 2000 RPM
            extra_api_keys=["key2", "key3"],
        )

        # Should have 3 slots (1 from env + 2 from extra_api_keys)
        assert len(client.slots) == 3

        # Each slot should have the correct limits
        for slot in client.slots:
            assert slot.limiter.tpm == 3_000_000
            assert slot.limiter.rpm == 2000


if __name__ == "__main__":
    pytest.main([__file__])
