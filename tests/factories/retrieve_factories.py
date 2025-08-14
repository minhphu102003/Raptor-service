from __future__ import annotations

from typing import Optional

from faker import Faker
from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import BaseModel

from app.dto.retrieve import RetrieveRequest

fake = Faker()


class RetrieveRequestFactory(ModelFactory[RetrieveRequest]):
    __model__ = RetrieveRequest

    @classmethod
    def tree_id(cls) -> str:
        return f"kb.{fake.slug()}.2025-08-14"

    @classmethod
    def query(cls) -> str:
        return fake.sentence(nb_words=10)
