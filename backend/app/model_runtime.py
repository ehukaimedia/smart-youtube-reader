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


def list_local_models() -> list[str]:
    try:
        return _model_names(_request_json("/api/tags", timeout=5))
    except Exception as exc:
        logger.warning("Could not list Ollama models: %s", exc)
        return []


def list_loaded_models() -> list[str]:
    try:
        return _model_names(_request_json("/api/ps", timeout=5))
    except Exception as exc:
        logger.warning("Could not list running Ollama models: %s", exc)
        return []


def model_info(model: str = DEFAULT_MODEL) -> dict:
    return _request_json("/api/show", {"model": model}, timeout=15)


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
    response_format: dict | str | None = None,
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
    if response_format is not None:
        payload["format"] = response_format
    data = _request_json("/api/chat", payload, timeout=timeout)
    message = data.get("message") or {}
    return str(message.get("content") or "")
