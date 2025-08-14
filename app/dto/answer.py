from __future__ import annotations

from pydantic import BaseModel


class AnswerRequest(BaseModel):
    retrieve: dict
    generation: dict
