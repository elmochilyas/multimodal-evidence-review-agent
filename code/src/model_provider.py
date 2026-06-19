"""Model provider abstraction for vision-capable review."""

import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class ModelProvider(ABC):
    """Abstract interface for a vision-capable model provider."""

    @abstractmethod
    def complete(
        self, system_prompt: str, user_prompt: str, images: List[str]
    ) -> str:
        """Send a prompt with images and return the model's text response."""
        ...


class MockProvider(ModelProvider):
    """Mock provider that returns a fixed or configurable response.

    Useful for tests and no-cost baseline runs.
    """

    def __init__(self, response: Optional[str] = None):
        self.response = response or self._default_response()
        self.calls: List[Dict[str, Any]] = []

    def _default_response(self) -> str:
        return (
            '{"evidence_standard_met": "false", '
            '"evidence_standard_met_reason": "Mock fallback: insufficient evidence", '
            '"risk_flags": ["manual_review_required"], '
            '"issue_type": "unknown", '
            '"object_part": "unknown", '
            '"claim_status": "not_enough_information", '
            '"claim_status_justification": "Mock provider did not inspect images.", '
            '"supporting_image_ids": ["none"], '
            '"valid_image": "false", '
            '"severity": "unknown"}'
        )

    def complete(
        self, system_prompt: str, user_prompt: str, images: List[str]
    ) -> str:
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "image_count": len(images),
            }
        )
        return self.response


class OpenAICompatibleProvider(ModelProvider):
    """Provider for OpenAI-compatible vision APIs (OpenAI, Azure, local servers, etc.)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.0,
    ):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.base_url = base_url or os.environ.get("OPENAI_BASE_URL")
        self.model = model or os.environ.get("VISION_MODEL", "gpt-4o")
        self.temperature = temperature
        self._client: Optional[Any] = None

    def _get_client(self) -> Any:
        """Lazy import and initialize the OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError as exc:
                raise ImportError(
                    "The 'openai' package is required for live model calls. "
                    "Install it with: pip install openai"
                ) from exc

            kwargs: Dict[str, Any] = {"api_key": self.api_key}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            self._client = OpenAI(**kwargs)
        return self._client

    def _build_messages(
        self, system_prompt: str, user_prompt: str, images: List[str]
    ) -> List[Dict[str, Any]]:
        content: List[Dict[str, Any]] = [
            {"type": "text", "text": user_prompt},
        ]
        for data_url in images:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": data_url, "detail": "auto"},
                }
            )

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content},
        ]

    def complete(
        self, system_prompt: str, user_prompt: str, images: List[str]
    ) -> str:
        client = self._get_client()
        messages = self._build_messages(system_prompt, user_prompt, images)

        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=2048,
        )

        if not response.choices:
            raise RuntimeError("Model returned no choices")

        return response.choices[0].message.content or ""


def create_provider(
    provider_name: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
) -> ModelProvider:
    """Factory for creating the configured model provider.

    Defaults to MockProvider if provider_name is missing or unrecognized.
    """
    name = (provider_name or os.environ.get("MODEL_PROVIDER", "mock")).lower().strip()

    if name == "openai_compatible":
        return OpenAICompatibleProvider(
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=temperature if temperature is not None else 0.0,
        )

    # Default to mock for safety and for tests/no-cost runs.
    return MockProvider()
