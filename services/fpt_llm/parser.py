import json
from typing import Any, Dict, Iterator


def parse_sse_lines(iter_lines) -> Iterator[str]:
    """
    Parse Server-Sent Events (SSE) and yield the content after the 'data:' prefix.
    Stops when a line with '[DONE]' is received.
    """
    for raw_line in iter_lines:
        if not raw_line:
            continue
        try:
            line = raw_line.decode("utf-8")
        except AttributeError:
            # already str
            line = raw_line
        line = line.strip()
        if not line:
            continue
        if line.startswith("data:"):
            data = line[len("data:") :].strip()
            if data == "[DONE]":
                break
            yield data
        # ignore other SSE fields like 'event:' or comments
