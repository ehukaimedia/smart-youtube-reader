from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from collections import deque
from pathlib import Path
from typing import Iterable

logger = logging.getLogger(__name__)

MLX_PORT = int(os.environ.get("MLX_PORT", "11435"))
MLX_HOST = os.environ.get("MLX_HOST", "127.0.0.1")
MLX_URL = f"http://{MLX_HOST}:{MLX_PORT}"
REPO_ROOT = Path(__file__).resolve().parents[2]
MLX_MODELS_DIR = Path(os.environ.get("MLX_MODELS_DIR", REPO_ROOT / "data" / "mlx"))

DEFAULT_MODEL = os.environ.get("SMART_READER_MODEL", "mlx-community/gemma-4-e4b-it-4bit")

AVAILABLE_MODELS = [
    {
        "name": "mlx-community/gemma-4-e2b-it-4bit",
        "label": "Gemma 4 E2B",
        "size": "3.6 GB",
        "recommended": False,
    },
    {
        "name": "mlx-community/gemma-4-e4b-it-4bit",
        "label": "Gemma 4 E4B",
        "size": "5.2 GB",
        "recommended": True,
    },
    {
        "name": "mlx-community/gemma-4-26b-a4b-it-4bit",
        "label": "Gemma 4 27B MoE",
        "size": "16 GB",
        "recommended": False,
    },
    {
        "name": "mlx-community/gemma-4-31b-it-4bit",
        "label": "Gemma 4 31B",
        "size": "18 GB",
        "recommended": False,
    },
]

_server_proc: subprocess.Popen | None = None
_current_model: str | None = None
_server_log: deque[str] = deque(maxlen=80)
_server_lock = threading.Lock()
_server_ready = threading.Condition(_server_lock)
_health_cache: tuple[str | None, float, bool] = (None, 0.0, False)
HEALTH_CACHE_SECONDS = 1.0


def supported_model_names() -> list[str]:
    return [model["name"] for model in AVAILABLE_MODELS]


def is_supported_model(model: str) -> bool:
    return model in supported_model_names()


def _request_json(path: str, payload: dict | None = None, timeout: int = 30) -> dict:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(f"{MLX_URL}{path}", data=data, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"MLX request failed: {exc.code} {exc.reason}: {body}") from exc


def list_loaded_models() -> list[str]:
    try:
        data = _request_json("/v1/models", timeout=2)
    except Exception:
        return []
    return [item.get("id") for item in data.get("data", []) if item.get("id")]


def mlx_available() -> bool:
    check = subprocess.run(
        [sys.executable, "-c", "import mlx_vlm"],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    if check.returncode != 0:
        logger.error("mlx-vlm is not importable from %s: %s", sys.executable, check.stderr.strip())
        return False
    return True


def ensure_server(model: str, timeout: int = 600) -> None:
    global _server_proc, _current_model

    if not is_supported_model(model):
        supported = ", ".join(supported_model_names())
        raise ValueError(f"Unsupported MLX model '{model}'. Supported models: {supported}")

    started_by_this_call = False
    started_at = time.time()

    while True:
        with _server_ready:
            if _is_healthy_for_model_locked(model):
                return

            proc = _server_proc
            current_model = _current_model
            running_requested_model = (
                proc is not None
                and proc.poll() is None
                and current_model == model
            )
            # The short cache may expire while video preprocessing runs. When the
            # requested server is already running, probe outside the lock below so
            # callers do not wait forever on stale cache state.
            if not running_requested_model:
                _stop_server_locked()

                if not mlx_available():
                    raise RuntimeError(
                        "mlx-vlm is not installed in the backend Python environment. "
                        "Run `pip install -r backend/requirements.txt` inside the backend venv."
                    )

                MLX_MODELS_DIR.mkdir(parents=True, exist_ok=True)
                env = os.environ.copy()
                env.setdefault("HF_HOME", str(MLX_MODELS_DIR))
                env.setdefault("TRANSFORMERS_CACHE", env["HF_HOME"])
                env.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
                cmd = [
                    sys.executable,
                    "-m",
                    "mlx_vlm.server",
                    "--model",
                    model,
                    "--host",
                    MLX_HOST,
                    "--port",
                    str(MLX_PORT),
                ]
                logger.info("Starting MLX server: %s", " ".join(cmd))
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=env,
                )
                _start_log_thread(proc.stdout, "stdout")
                _start_log_thread(proc.stderr, "stderr")

                _server_proc = proc
                _current_model = model
                started_by_this_call = True
                break

        if _is_healthy_for_model(model):
            return
        if time.time() - started_at >= timeout:
            raise RuntimeError(
                f"MLX server did not become healthy within {timeout}s. Recent log: {_recent_log()}"
            )
        time.sleep(1.5)

    if started_by_this_call:
        try:
            _wait_for_health(model, timeout)
        finally:
            with _server_ready:
                _server_ready.notify_all()


def _is_healthy_for_model_locked(model: str) -> bool:
    if _server_proc is not None and _server_proc.poll() is not None:
        return False
    cached_model, checked_at, healthy = _health_cache
    if cached_model == model and time.time() - checked_at <= HEALTH_CACHE_SECONDS:
        return healthy
    return False


def _is_healthy_for_model(model: str) -> bool:
    global _health_cache
    with _server_ready:
        if _is_healthy_for_model_locked(model):
            return True
        if _server_proc is not None and _server_proc.poll() is not None:
            _health_cache = (model, time.time(), False)
            return False
        expected_model = _current_model

    loaded = list_loaded_models()
    healthy = model in loaded or (bool(loaded) and expected_model == model)

    with _server_ready:
        _health_cache = (model, time.time(), healthy)
        return healthy


def _wait_for_health(model: str, timeout: int) -> None:
    started_at = time.time()
    last_error: Exception | None = None
    while time.time() - started_at < timeout:
        if _is_healthy_for_model(model):
            logger.info("MLX server is healthy for %s", model)
            return
        with _server_ready:
            proc = _server_proc
            if proc is not None and proc.poll() is not None:
                raise RuntimeError(
                    f"MLX server exited with code {proc.returncode}. Recent log: {_recent_log()}"
                )
        try:
            _request_json("/v1/models", timeout=2)
        except Exception as exc:
            last_error = exc
        time.sleep(1.5)
    raise RuntimeError(
        f"MLX server did not become healthy within {timeout}s. "
        f"Last error: {last_error}. Recent log: {_recent_log()}"
    )


def _stop_server_locked() -> None:
    global _server_proc, _current_model, _health_cache
    if _server_proc is not None and _server_proc.poll() is None:
        logger.info("Stopping MLX server for %s", _current_model)
        _server_proc.terminate()
        try:
            _server_proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            _server_proc.kill()
    _server_proc = None
    _current_model = None
    _health_cache = (None, 0.0, False)


def _start_log_thread(pipe, stream_name: str) -> None:
    if pipe is None:
        return

    def drain() -> None:
        for line in iter(pipe.readline, ""):
            text = line.strip()
            if text:
                _server_log.append(f"{stream_name}: {text}")
                logger.info("[mlx] %s", text)

    thread = threading.Thread(target=drain, daemon=True)
    thread.start()


def _recent_log() -> str:
    return " | ".join(_server_log)[-1200:]


def chat(model: str, messages: Iterable[dict], temperature: float = 0.2, max_tokens: int = 8192) -> str:
    ensure_server(model)
    payload = {
        "model": model,
        "messages": [
            {"role": message.get("role", "user"), "content": message.get("content", "")}
            for message in messages
        ],
        "stream": True,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    request = urllib.request.Request(
        f"{MLX_URL}/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Accept": "text/event-stream", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=900) as response:
            return _read_chat_stream(response)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"MLX chat failed: {exc.code} {exc.reason}: {body}") from exc


def _read_chat_stream(response) -> str:
    parts: list[str] = []
    for raw_line in response:
        line = raw_line.decode("utf-8", errors="replace").strip()
        if not line or not line.startswith("data:"):
            continue
        data = line.removeprefix("data:").strip()
        if data == "[DONE]":
            break
        try:
            event = json.loads(data)
        except json.JSONDecodeError:
            continue
        choices = event.get("choices") or []
        if not choices:
            continue
        delta = choices[0].get("delta") or {}
        content = delta.get("content")
        if content:
            parts.append(str(content))
        if choices[0].get("finish_reason") in {"stop", "length"}:
            break
    return "".join(parts)
