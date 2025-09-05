from __future__ import annotations

from typing import Optional

from faker import Faker
from polyfactory.factories.pydantic_factory import ModelFactory

from services.retrieval.retrieval_service import RetrieveBody

fake = Faker()


class RetrieveBodyFactory(ModelFactory[RetrieveBody]):
    __model__ = RetrieveBody

    @classmethod
    def dataset_id(cls) -> str:
        return f"kb.{fake.slug()}.2025-08-14"

    @classmethod
    def query(cls) -> str:
        return fake.sentence(nb_words=10)

    @classmethod
    def mode(cls) -> str:
        return "collapsed"

    @classmethod
    def top_k(cls) -> int:
        return 5

    @classmethod
    def expand_k(cls) -> int:
        return 3

    @classmethod
    def levels_cap(cls) -> int:
        return 0

    @classmethod
    def use_reranker(cls) -> bool:
        return False

    @classmethod
    def reranker_model(cls) -> Optional[str]:
        return None

    @classmethod
    def byok_voyage_api_key(cls) -> Optional[str]:
        return None
