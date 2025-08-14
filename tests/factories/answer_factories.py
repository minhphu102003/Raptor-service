from __future__ import annotations

from faker import Faker
from polyfactory.factories.pydantic_factory import ModelFactory

from app.dto import AnswerRequest

fake = Faker()


class AnswerRequestFactory(ModelFactory[AnswerRequest]):
    __model__ = AnswerRequest

    @classmethod
    def retrieve(cls) -> dict:
        return {
            "tree_id": f"kb.{fake.slug()}.2025-08-14",
            "mode": "collapsed",
            "query": fake.sentence(),
            "top_k": 6,
        }

    @classmethod
    def generation(cls) -> dict:
        return {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "max_tokens": 256,
            "stream": False,
            "cite_sources": True,
        }
