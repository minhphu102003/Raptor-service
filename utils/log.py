def preview(txt: str, n: int = 120) -> str:
    if txt is None:
        return "<None>"
    s = txt.replace("\n", " ")
    return (s[:n] + "…") if len(s) > n else s
