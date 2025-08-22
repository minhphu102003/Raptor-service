import re


def clean_summary(text: str) -> str:
    return re.sub(r"^Summary:\s*", "", text, count=1, flags=re.IGNORECASE)
