"""File-based caching for model responses."""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def _make_cache_key(
    claim_row: Dict[str, str],
    image_paths: List[str],
    model_name: str,
    prompt_version: str,
) -> str:
    """Create a deterministic cache key from claim data and run context."""
    key_data = {
        "user_id": claim_row.get("user_id", ""),
        "user_claim": claim_row.get("user_claim", ""),
        "claim_object": claim_row.get("claim_object", ""),
        "image_paths": image_paths,
        "model_name": model_name,
        "prompt_version": prompt_version,
    }
    serialized = json.dumps(key_data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class ModelResponseCache:
    """Simple file-based cache for raw model response strings."""

    def __init__(self, cache_dir: str = ".cache/model_responses"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _cache_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"

    def get(
        self,
        claim_row: Dict[str, str],
        image_paths: List[str],
        model_name: str,
        prompt_version: str,
    ) -> Optional[str]:
        """Return cached response string or None."""
        key = _make_cache_key(claim_row, image_paths, model_name, prompt_version)
        path = self._cache_path(key)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data.get("response")
        except Exception:  # pragma: no cover - defensive
            return None

    def set(
        self,
        claim_row: Dict[str, str],
        image_paths: List[str],
        model_name: str,
        prompt_version: str,
        response: str,
    ) -> None:
        """Cache a response string."""
        key = _make_cache_key(claim_row, image_paths, model_name, prompt_version)
        path = self._cache_path(key)
        path.write_text(
            json.dumps({"response": response}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def clear(self) -> None:
        """Remove all cached entries."""
        for path in self.cache_dir.glob("*.json"):
            path.unlink()
