class ModelRegistry:
    def __init__(
        self, *, fpt_client, openai_client=None, gemini_client=None, anthropic_client=None
    ):
        self.fpt = fpt_client
        self.openai = openai_client
        self.gemini = gemini_client
        self.anthropic = anthropic_client

        self._route = {
            # DeepSeek
            "deepseek-v3": "fpt",
            "deepseek": "fpt",
            # OpenAI
            "gpt-4o-mini": "openai",
            "gpt4o-mini": "openai",
            # Gemini
            "gemini-1.5-pro": "gemini",
            "gemini-15-pro": "gemini",
            "gemini-2.5-flash": "gemini",
            "gemini-25-flash": "gemini",
            "gemini25flash": "gemini",
            "gemini2.5flash": "gemini",
            # Anthropic
            "claude-3.5-haiku": "anthropic",
            "claude35haiku": "anthropic",
            "claude-3-5-haiku": "anthropic",
        }

        self._pretty = {
            "fpt": "DeepSeek-V3",
            "openai": "GPT-4o-mini",
            "gemini": "Gemini (1.5 Pro / 2.5 Flash)",
            "anthropic": "Claude-3.5-Haiku",
        }

    @staticmethod
    def _norm(name: str) -> str:
        return (name or "").strip().lower().replace(" ", "").replace("_", "-")

    def get_client(self, name: str, body=None):
        key = self._norm(name)
        target = self._route.get(key)
        if not target:
            supported = sorted({k for k in self._route.keys()})
            raise ValueError(f"Unsupported model: {name}. Supported aliases: {supported}")

        client = getattr(self, target, None)
        if client is None:
            raise ValueError(f"Client for {self._pretty.get(target, target)} is not configured")

        return client
