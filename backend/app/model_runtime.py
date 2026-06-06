from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from typing import Iterable

logger = logging.getLogger(__name__)

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
DEFAULT_MODEL = os.environ.get("SMART_READER_MODEL", "gemma4:12b")

AVAILABLE_MODELS = [
    {
        "name": "gemma4:12b",
        "label": "Gemma 4 12B",
        "size": "7.6 GB",
        "recommended": True,
        "provider": "ollama",
        "capabilities": ["text", "image"],
    },
    {
        "name": "gemma4:e4b",
        "label": "Gemma 4 E4B",
        "size": "9.6 GB",
        "recommended": False,
        "provider": "ollama",
        "capabilities": ["text", "image"],
    },
    {
        "name": "gemma4:26b",
        "label": "Gemma 4 26B",
        "size": "18 GB",
        "recommended": False,
        "provider": "ollama",
        "capabilities": ["text", "image"],
    },
    {
        "name": "gemma4:31b",
        "label": "Gemma 4 31B",
        "size": "20 GB",
        "recommended": False,
        "provider": "ollama",
        "capabilities": ["text", "image"],
    },
]


def _request_json(path: str, payload: dict | None = None, timeout: int = 30) -> dict:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(f"{OLLAMA_HOST}{path}", data=data, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Ollama request failed: {exc.code} {exc.reason}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Ollama is not reachable at {OLLAMA_HOST}. Start Ollama and pull `{DEFAULT_MODEL}`."
        ) from exc


def _model_names(data: dict) -> list[str]:
    return [
        str(item.get("name") or item.get("model"))
        for item in data.get("models", [])
        if item.get("name") or item.get("model")
    ]


def list_local_model_details() -> list[dict]:
    try:
        data = _request_json("/api/tags", timeout=5)
    except Exception as exc:
        logger.warning("Could not list Ollama models: %s", exc)
        return []
    return [item for item in data.get("models", []) if isinstance(item, dict)]


def list_local_models() -> list[str]:
    return _model_names({"models": list_local_model_details()})


def list_loaded_models() -> list[str]:
    try:
        return _model_names(_request_json("/api/ps", timeout=5))
    except Exception as exc:
        logger.warning("Could not list running Ollama models: %s", exc)
        return []


def model_info(model: str = DEFAULT_MODEL) -> dict:
    return _request_json("/api/show", {"model": model}, timeout=15)


def _catalog_entry(model: str) -> dict:
    for item in AVAILABLE_MODELS:
        if item["name"] == model:
            return item
    return {"name": model, "provider": "ollama", "capabilities": []}


def _local_model_entry(model: str, details: list[dict] | None = None) -> dict | None:
    for item in details if details is not None else list_local_model_details():
        if item.get("name") == model or item.get("model") == model:
            return item
    return None


def runtime_metadata(model: str = DEFAULT_MODEL) -> dict:
    catalog = _catalog_entry(model)
    local = _local_model_entry(model)
    metadata = {
        "provider": catalog.get("provider", "ollama"),
        "model": model,
        "host": OLLAMA_HOST,
        "capabilities": list(catalog.get("capabilities", [])),
        "installed": local is not None,
    }
    if not local:
        return metadata

    for key in ("digest", "size", "modified_at"):
        value = local.get(key)
        if value is not None:
            metadata[key] = value

    details = local.get("details")
    if isinstance(details, dict):
        model_details = {
            key: details[key]
            for key in ("family", "families", "parameter_size", "quantization_level")
            if key in details
        }
        if model_details:
            metadata["details"] = model_details

    return metadata


def check_model(model: str = DEFAULT_MODEL) -> bool:
    if model in list_local_models():
        return True
    raise RuntimeError(
        f"Ollama model `{model}` is not installed. Run `ollama pull {model}` and retry."
    )


def _normalize_message(message: dict) -> dict:
    normalized = {
        "role": message.get("role", "user"),
        "content": message.get("content", ""),
    }
    images = message.get("images")
    if images:
        normalized["images"] = images
    return normalized


def chat(
    model: str,
    messages: Iterable[dict],
    temperature: float = 0.2,
    max_tokens: int = 8192,
    timeout: int = 900,
) -> str:
    check_model(model)
    payload = {
        "model": model,
        "messages": [_normalize_message(message) for message in messages],
        "stream": False,
        "think": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }
    data = _request_json("/api/chat", payload, timeout=timeout)
    message = data.get("message") or {}
    return str(message.get("content") or "")
