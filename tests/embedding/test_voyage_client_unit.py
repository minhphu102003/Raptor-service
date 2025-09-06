"""
Unit tests for VoyageEmbeddingClientAsync class
"""

import asyncio
import os
from unittest.mock import AsyncMock, Mock, patch

import pytest

from services.providers.voyage.voyage_client import VoyageEmbeddingClientAsync


class TestVoyageEmbeddingClientAsync:
    """Test suite for VoyageEmbeddingClientAsync class"""

    @pytest.fixture
    def mock_env(self, monkeypatch):
        """Fixture to set up environment variables for testing"""
        monkeypatch.setenv("VOYAGEAI_KEY", "test-api-key")
        yield
        monkeypatch.delenv("VOYAGEAI_KEY", raising=False)

    @pytest.fixture
    def client(self, mock_env):
        """Fixture to create a client instance for testing"""
        return VoyageEmbeddingClientAsync(model="voyage-context-3", out_dim=1024, out_dtype="float")

    # Test API Key Management
    def test_collect_api_keys_deduplication(self, monkeypatch):
        """Test deduplication of API keys"""
        # Clear any existing Voyage environment variables that might interfere
        monkeypatch.delenv("VOYAGEAI_KEY", raising=False)
        monkeypatch.delenv("VOYAGEAI_KEY_1", raising=False)
        monkeypatch.delenv("VOYAGEAI_KEY_2", raising=False)
        monkeypatch.delenv("VOYAGEAI_KEY_3", raising=False)

        monkeypatch.setenv("VOYAGEAI_KEY", "key1")
        monkeypatch.setenv("VOYAGEAI_KEY_1", "key1")  # Duplicate
        monkeypatch.setenv("VOYAGEAI_KEY_2", "key2")  # Unique

        client = VoyageEmbeddingClientAsync(extra_api_keys=["key1", "key3"])
        # Should have 3 unique keys: key1, key2, key3
        assert len(client.keys) == 3
        assert "key1" in client.keys
        assert "key2" in client.keys
        assert "key3" in client.keys

    # Test Client Initialization
    def test_default_initialization(self, monkeypatch):
        """Test default initialization parameters"""
        # Clear any existing Voyage environment variables that might interfere
        monkeypatch.delenv("VOYAGEAI_KEY", raising=False)
        monkeypatch.delenv("VOYAGEAI_KEY_1", raising=False)
        monkeypatch.delenv("VOYAGEAI_KEY_2", raising=False)
        monkeypatch.delenv("VOYAGEAI_KEY_3", raising=False)

        monkeypatch.setenv("VOYAGEAI_KEY", "test-api-key")

        client = VoyageEmbeddingClientAsync()
        assert client.model == "voyage-context-3"
        assert client.out_dim == 1024
        assert client.out_dtype == "float"
        assert client.max_retries == 3
        assert len(client.slots) == 1

    def test_custom_initialization(self, monkeypatch):
        """Test custom initialization parameters"""
        # Clear any existing Voyage environment variables that might interfere
        monkeypatch.delenv("VOYAGEAI_KEY", raising=False)
        monkeypatch.delenv("VOYAGEAI_KEY_1", raising=False)
        monkeypatch.delenv("VOYAGEAI_KEY_2", raising=False)
        monkeypatch.delenv("VOYAGEAI_KEY_3", raising=False)

        monkeypatch.setenv("VOYAGEAI_KEY", "test-api-key")

        client = VoyageEmbeddingClientAsync(
            model="voyage-lite-2",
            out_dim=512,
            out_dtype="int",
            rpm_limit=5,
            tpm_limit=20000,
            max_retries=5,
        )
        assert client.model == "voyage-lite-2"
        assert client.out_dim == 512
        assert client.out_dtype == "int"
        assert client.max_retries == 5

    # Test Slot Management
    def test_slot_creation(self, monkeypatch):
        """Test slot creation with multiple API keys"""
        # Clear any existing Voyage environment variables that might interfere
        monkeypatch.delenv("VOYAGEAI_KEY", raising=False)
        monkeypatch.delenv("VOYAGEAI_KEY_1", raising=False)
        monkeypatch.delenv("VOYAGEAI_KEY_2", raising=False)
        monkeypatch.delenv("VOYAGEAI_KEY_3", raising=False)

        monkeypatch.setenv("VOYAGEAI_KEY", "test-api-key")

        client = VoyageEmbeddingClientAsync(extra_api_keys=["key2", "key3"])
        assert len(client.slots) == 3  # 1 from env + 2 from extra_api_keys

    # Test Text Chunking
    def test_pack_groups_by_tpm_normal(self, client):
        """Test normal text chunking"""
        chunks = ["short text", "another short text", "yet another piece"]
        groups = client._pack_groups_by_tpm(chunks)
        # All chunks should fit in one group since they're small
        assert len(groups) == 1
        assert groups[0] == chunks

    # Test Embedding Functionality (with mocking)
    @pytest.mark.asyncio
    async def test_embed_queries_success(self, client):
        """Test successful query embedding"""
        # Mock the API response
        mock_response = Mock()
        mock_result = Mock()
        mock_result.embeddings = [[0.1, 0.2, 0.3]]
        mock_response.results = [mock_result]

        # Mock the client's contextualized_embed method
        with patch.object(
            client.slots[0].client, "contextualized_embed", AsyncMock(return_value=mock_response)
        ):
            queries = ["test query"]
            result = await client.embed_queries(queries)
            assert len(result) == 1
            assert result[0] == [0.1, 0.2, 0.3]

    @pytest.mark.asyncio
    async def test_embed_doc_fulltext_multi_success(self, client):
        """Test successful document embedding"""
        # Mock the API response
        mock_response = Mock()
        mock_result = Mock()
        mock_result.embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        mock_response.results = [mock_result]

        # Mock the client's contextualized_embed method
        with patch.object(
            client.slots[0].client, "contextualized_embed", AsyncMock(return_value=mock_response)
        ):
            text = "This is a test document with multiple sentences."
            result_embeddings, result_chunks = await client.embed_doc_fulltext_multi(text)
            assert len(result_embeddings) == 2
            assert len(result_chunks) == 1  # One group

    # Test Rate Limit Configuration
    def test_voyage_context_3_rate_limits_configuration(self, monkeypatch):
        """Test configuration of voyage-context-3 rate limits"""
        # Clear any existing Voyage environment variables that might interfere
        monkeypatch.delenv("VOYAGEAI_KEY", raising=False)
        monkeypatch.delenv("VOYAGEAI_KEY_1", raising=False)
        monkeypatch.delenv("VOYAGEAI_KEY_2", raising=False)
        monkeypatch.delenv("VOYAGEAI_KEY_3", raising=False)

        monkeypatch.setenv("VOYAGEAI_KEY", "test-key")

        # Create client with voyage-context-3 model
        client = VoyageEmbeddingClientAsync(
            model="voyage-context-3",
            tpm_limit=3_000_000,  # 3M TPM
            rpm_limit=2000,  # 2000 RPM
        )

        # Verify configuration
        assert client.model == "voyage-context-3"
        assert len(client.slots) == 1
        slot = client.slots[0]
        assert slot.limiter.tpm == 3_000_000
        assert slot.limiter.rpm == 2000


if __name__ == "__main__":
    pytest.main([__file__])
