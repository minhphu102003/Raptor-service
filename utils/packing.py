from typing import List

import voyageai


def token_lengths(texts: List[str], model: str, api_key: str) -> List[int]:
    cli = voyageai.Client(api_key=api_key)
    encs = cli.tokenize(texts=texts, model=model)
    return [len(enc.ids) for enc in encs]


def count_tokens_total(texts: List[str], model: str, api_key: str) -> int:
    if isinstance(texts, str):
        texts = [texts]
    cli = voyageai.Client(api_key=api_key)
    return cli.count_tokens(texts=texts, model=model)
