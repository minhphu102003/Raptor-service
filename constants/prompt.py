from langchain_core.prompts import ChatPromptTemplate

LLM_EDGE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a chunk-boundary organizer for RAG. "
            "MANDATORY RULE: DO NOT ADD NEW INFORMATION. "
            "You may only reuse, combine, or shorten words/phrases that EXIST IN THE PROVIDED WINDOW. "
            "If you cannot rewrite a sentence due to insufficient evidence, return null.",
        ),
        (
            "human",
            "Boundary window between A and B (each side up to 5 sentences):\n\n"
            "A (tail):\n{a_tail}\n\nB (head):\n{b_head}\n\n"
            "Requirements:\n"
            "1) Decide how many sentences to move from A→B (0..5) and from B→A (0..5).\n"
            "2) If the LAST sentence of A is cut, rewrite that sentence USING ONLY words from the window; "
            "   if not needed, set it to null.\n"
            "3) If the FIRST sentence of B is cut, rewrite that sentence USING ONLY words from the window; "
            "   if not needed, set it to null.\n\n"
            "Return STRICT JSON matching this schema:\n"
            '{{"move_a_to_b": <int 0..5>, "move_b_to_a": <int 0..5>, '
            '"rewrite_a_last": <string|null>, "rewrite_b_first": <string|null>}}',
        ),
    ]
)


REWRITE_SYSTEM_PROMPT = (
    "You are a query rewriter for a RAG retrieval system.\n"
    "- Rewrite the user's query into a concise, self-contained search query.\n"
    "- Keep key entities, intents, constraints; remove chit-chat.\n"
    "- Do NOT invent facts. Preserve language (vi/en) as in input.\n"
    "- Prefer nouns, verbs, and filters; avoid fluff.\n"
    "- Return ONLY the rewritten query text."
)
