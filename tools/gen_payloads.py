from __future__ import annotations

import json
import os
import random

from faker import Faker
import numpy as np
import typer

from tests.factories import AnswerRequestFactory, BuildRequestFactory, RetrieveRequestFactory

app = typer.Typer(help="Generate sample request bodies for RAPTOR Service")


@app.command()
def build(count: int = 3, seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)
    Faker.seed(seed)
    os.makedirs("samples/requests", exist_ok=True)
    for i in range(count):
        req = BuildRequestFactory.build()
        with open(f"samples/requests/build_{i + 1}.json", "w", encoding="utf-8") as f:
            json.dump(json.loads(req.model_dump_json()), f, ensure_ascii=False, indent=2)


@app.command()
def retrieve(count: int = 3, seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)
    Faker.seed(seed)
    os.makedirs("samples/requests", exist_ok=True)
    for i in range(count):
        req = RetrieveRequestFactory.build()
        with open(f"samples/requests/retrieve_{i + 1}.json", "w", encoding="utf-8") as f:
            json.dump(json.loads(req.model_dump_json()), f, ensure_ascii=False, indent=2)


@app.command()
def answer(count: int = 2, seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)
    Faker.seed(seed)
    os.makedirs("samples/requests", exist_ok=True)
    for i in range(count):
        req = AnswerRequestFactory.build()
        with open(f"samples/requests/answer_{i + 1}.json", "w", encoding="utf-8") as f:
            json.dump(json.loads(req.model_dump_json()), f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    app()
