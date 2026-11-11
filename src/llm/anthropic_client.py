"""Anthropic Claude client shared by LLM-backed agents (default model: Claude Haiku).

Configuration (config/settings.yaml -> `llm:`), overridable by environment variables:
  - ANTHROPIC_API_KEY            API key (env var name configurable via `llm.api_key_env`)
  - XML_PIPELINE_LLM_MODEL       overrides `llm.model`
  - XML_PIPELINE_LLM_ENABLED     overrides `llm.enabled` (true/false)

Verify your key and model with:
    python -m src.llm.anthropic_client
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

SETTINGS_PATH = Path(__file__).resolve().parents[2] / "config" / "settings.yaml"
DEFAULT_MODEL = "claude-haiku-5-5"


class LLMError(RuntimeError):
    """Raised when the LLM is unavailable or returns an unusable response."""


@dataclass(frozen=True)
class LLMConfig:
    enabled: bool
    provider: str
    model: str
    max_tokens: int
    temperature: float
    timeout_seconds: float
    max_retries: int
    send_sample_values: bool
    fail_if_unavailable: bool
    api_key_env: str

    @property
    def api_key(self) -> str | None:
        return os.environ.get(self.api_key_env) or None

    @property
    def is_available(self) -> bool:
        return self.enabled and self.provider == "anthropic" and bool(self.api_key)


def _env_bool(name: str) -> bool | None:
    val = os.environ.get(name)
    if val is None:
        return None
    return val.strip().lower() in ("1", "true", "yes", "on")


def load_llm_config(settings_path: Path = SETTINGS_PATH) -> LLMConfig:
    raw: dict[str, Any] = {}
    if settings_path.exists():
        raw = (yaml.safe_load(settings_path.read_text(encoding="utf-8")) or {}).get("llm") or {}

    enabled_override = _env_bool("XML_PIPELINE_LLM_ENABLED")
    return LLMConfig(
        enabled=bool(raw.get("enabled", True)) if enabled_override is None else enabled_override,
        provider=str(raw.get("provider", "anthropic")),
        model=os.environ.get("XML_PIPELINE_LLM_MODEL") or str(raw.get("model", DEFAULT_MODEL)),
        max_tokens=int(raw.get("max_tokens", 16000)),
        temperature=float(raw.get("temperature", 0.0)),
        timeout_seconds=float(raw.get("timeout_seconds", 120)),
        max_retries=int(raw.get("max_retries", 3)),
        send_sample_values=bool(raw.get("send_sample_values", True)),
        fail_if_unavailable=bool(raw.get("fail_if_unavailable", False)),
        api_key_env=str(raw.get("api_key_env", "ANTHROPIC_API_KEY")),
    )


class ClaudeClient:
    """Thin wrapper around the Anthropic Messages API that returns schema-shaped JSON via forced tool use."""

    def __init__(self, config: LLMConfig | None = None, client: Any | None = None) -> None:
        self.config = config or load_llm_config()
        if client is not None:
            self._client = client  # injected (tests / custom transport)
            return
        if not self.config.api_key:
            raise LLMError(f"{self.config.api_key_env} is not set")
        try:
            import anthropic
        except ImportError as exc:  # pragma: no cover
            raise LLMError("The 'anthropic' package is not installed. Run: pip install anthropic") from exc
        self._client = anthropic.Anthropic(
            api_key=self.config.api_key,
            timeout=self.config.timeout_seconds,
            max_retries=self.config.max_retries,
        )

    @property
    def model(self) -> str:
        return self.config.model

    def call_tool(
        self,
        *,
        system: str,
        prompt: str,
        tool_name: str,
        tool_description: str,
        input_schema: dict[str, Any],
    ) -> dict[str, Any]:
        """Force Claude to answer by calling `tool_name`, and return the tool input as a dict."""
        try:
            resp = self._client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system=system,
                messages=[{"role": "user", "content": prompt}],
                tools=[{"name": tool_name, "description": tool_description, "input_schema": input_schema}],
                tool_choice={"type": "tool", "name": tool_name},
            )
        except Exception as exc:  # anthropic.APIError, network errors, etc.
            raise LLMError(f"Anthropic API call failed (model={self.config.model}): {exc}") from exc

        if getattr(resp, "stop_reason", None) == "max_tokens":
            raise LLMError(
                f"Claude response was truncated at max_tokens={self.config.max_tokens}; increase llm.max_tokens"
            )
        for block in getattr(resp, "content", []) or []:
            if getattr(block, "type", None) == "tool_use" and getattr(block, "name", None) == tool_name:
                return dict(block.input)
        raise LLMError(f"Claude did not return a '{tool_name}' tool call")


def main() -> None:
    """Connectivity check: prints config, lists available Haiku models, and pings the configured model."""
    cfg = load_llm_config()
    print(f"provider={cfg.provider} model={cfg.model} enabled={cfg.enabled} api_key_set={bool(cfg.api_key)}")
    if not cfg.api_key:
        print(f"Set {cfg.api_key_env} to enable Claude-backed agents.")
        raise SystemExit(1)

    import anthropic

    client = anthropic.Anthropic(api_key=cfg.api_key)
    model_ids = [m.id for m in client.models.list(limit=100)]
    print("Available Haiku models:", [m for m in model_ids if "haiku" in m] or "none")
    if not any(mid == cfg.model or mid.startswith(cfg.model) for mid in model_ids):
        print(f"WARNING: configured model '{cfg.model}' was not found in models.list(); update llm.model.")

    resp = client.messages.create(
        model=cfg.model,
        max_tokens=16,
        messages=[{"role": "user", "content": "Reply with the single word OK."}],
    )
    print("Ping response:", "".join(getattr(b, "text", "") for b in resp.content).strip())


if __name__ == "__main__":
    main()

