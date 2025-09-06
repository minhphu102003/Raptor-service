"""
Simple test to verify VoyageEmbeddingClientAsync basic functionality
"""

import os
from unittest.mock import patch

import pytest

from services.providers.voyage.voyage_client import VoyageEmbeddingClientAsync


def test_client_initialization(monkeypatch):
    """Test that client can be initialized with environment variable"""
    # Clear any existing Voyage environment variables that might interfere
    monkeypatch.delenv("VOYAGEAI_KEY", raising=False)
    monkeypatch.delenv("VOYAGEAI_KEY_1", raising=False)
    monkeypatch.delenv("VOYAGEAI_KEY_2", raising=False)
    monkeypatch.delenv("VOYAGEAI_KEY_3", raising=False)

    # Explicitly set only the environment variable we want
    monkeypatch.setenv("VOYAGEAI_KEY", "test-key")

    client = VoyageEmbeddingClientAsync()
    assert client is not None
    assert len(client.keys) == 1
    assert client.keys[0] == "test-key"


def test_client_initialization_without_api_key(monkeypatch):
    """Test that client raises error without API key"""
    # Remove any existing VOYAGEAI_KEY from environment
    monkeypatch.delenv("VOYAGEAI_KEY", raising=False)
    monkeypatch.delenv("VOYAGEAI_KEY_1", raising=False)
    monkeypatch.delenv("VOYAGEAI_KEY_2", raising=False)
    monkeypatch.delenv("VOYAGEAI_KEY_3", raising=False)

    with pytest.raises(RuntimeError, match="No Voyage API key provided"):
        VoyageEmbeddingClientAsync()


if __name__ == "__main__":
    pytest.main([__file__])
