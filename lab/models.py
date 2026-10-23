"""Model clients for the lab.

Reads configuration from the environment so no model name is hard-coded.
Defaults match a local Ollama install; set MODEL_BACKEND=claude to use the API.

    MODEL_BACKEND   ollama (default) | claude
    OLLAMA_MODEL    default: gemma4:e4b
    OLLAMA_HOST     default: http://localhost:11434
    ANTHROPIC_MODEL default: claude-opus-4-8   (only used when backend=claude)

The client exposes one method, complete(system, user) -> str, so an
investigation can swap backends without changing its own code.
"""

from __future__ import annotations

import json
import os
import urllib.request


class ModelError(RuntimeError):
    pass


def _post_json(url: str, payload: dict, timeout: int = 180) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001 - surfaced verbatim to the caller
        raise ModelError(f"request to {url} failed: {exc}") from exc


class OllamaClient:
    def __init__(self, model: str | None = None, host: str | None = None):
        self.model = model or os.environ.get("OLLAMA_MODEL", "gemma4:e4b")
        self.host = (host or os.environ.get("OLLAMA_HOST", "http://localhost:11434")).rstrip("/")

    def complete(self, system: str, user: str) -> str:
        out = _post_json(
            f"{self.host}/api/chat",
            {
                "model": self.model,
                "stream": False,
                "options": {"temperature": 0},
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
        )
        try:
            return out["message"]["content"]
        except (KeyError, TypeError) as exc:
            raise ModelError(f"unexpected Ollama response shape: {out!r}") from exc

    def label(self) -> str:
        return f"ollama:{self.model}"


class ClaudeClient:
    """Thin wrapper over the Anthropic SDK. Imported lazily so the lab runs
    with no SDK installed as long as the Ollama backend is used."""

    def __init__(self, model: str | None = None):
        self.model = model or os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-8")
        try:
            import anthropic  # noqa: F401
        except ImportError as exc:
            raise ModelError("MODEL_BACKEND=claude needs `pip install anthropic`") from exc
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise ModelError("MODEL_BACKEND=claude needs ANTHROPIC_API_KEY in the environment")
        import anthropic

        self._client = anthropic.Anthropic()

    def complete(self, system: str, user: str) -> str:
        msg = self._client.messages.create(
            model=self.model,
            max_tokens=1024,
            temperature=0,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(block.text for block in msg.content if getattr(block, "type", None) == "text")

    def label(self) -> str:
        return f"claude:{self.model}"


def get_client():
    backend = os.environ.get("MODEL_BACKEND", "ollama").lower()
    if backend == "ollama":
        return OllamaClient()
    if backend == "claude":
        return ClaudeClient()
    raise ModelError(f"unknown MODEL_BACKEND={backend!r} (use ollama or claude)")
