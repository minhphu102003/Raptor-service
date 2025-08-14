from __future__ import annotations

import random
import secrets
from typing import List

from faker import Faker
import numpy as np
from polyfactory import PostGenerated, Use
from polyfactory.factories.pydantic_factory import ModelFactory

from app.dto import BuildParams, BuildRequest, EmbeddingSpec, NodeIn

fake = Faker("en_US")


def _pick_model(_, values: dict) -> str:
    prov = values["provider"]

    return {
        "openai": "text-embedding-3-small",
        "cohere": "embed-english-v3.0",
        "huggingface": "BAAI/bge-small-en-v1.5",
    }[prov]


def l2_normalize(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v) or 1.0
    return (v / n).astype(np.float32)


def rand_embedding(dim: int, normalized: bool = True) -> List[float]:
    v = np.random.normal(0, 1, size=(dim,))
    if normalized:
        v = l2_normalize(v)
    return v.tolist()


class EmbeddingSpecFactory(ModelFactory[EmbeddingSpec]):
    __model__ = EmbeddingSpec
    provider = Use(ModelFactory.__random__.choice, ["openai", "cohere", "huggingface"])
    model = PostGenerated(_pick_model)
    embedding_dim = Use(ModelFactory.__random__.choice, [384, 512, 768, 1024, 1536])
    space = "cosine"
    normalized = True


class NodeFactory:
    @staticmethod
    def build(dim: int, with_embedding: bool = True) -> NodeIn:
        text = fake.paragraph(nb_sentences=3)
        meta = {"source": f"file://{fake.file_name()}", "page": random.randint(1, 10)}
        node: NodeIn = {"chunk_id": f"c_{fake.unique.bothify('#' * 4)}", "text": text, "meta": meta}
        if with_embedding:
            node["embedding"] = rand_embedding(dim, normalized=True)
        return node


class BuildRequestFactory(ModelFactory[BuildRequest]):
    __model__ = BuildRequest

    @classmethod
    def dataset_id(cls) -> str:
        return f"kb.{fake.slug()}"

    @classmethod
    def embedding_spec(cls) -> EmbeddingSpec:
        return EmbeddingSpecFactory.build()

    @classmethod
    def nodes(cls) -> List[NodeIn]:
        spec = cls.embedding_spec()
        return [
            NodeFactory.build(spec.embedding_dim, with_embedding=True)
            for _ in range((secrets.randbelow(20 - 8 + 1) + 8))
        ]

    @classmethod
    def params(cls) -> BuildParams:
        return BuildParams()
