# Reviewer A Backend Ollama Digest Audit - 2026-05-09

## Findings

### [P1] Installed Ollama digest model is reported unavailable

- File: `backend/app/digest.py:309`
- Spec: `docs/specs/ollama-ai-digest.md:18`

`_ollama_model_available()` compares the requested model name exactly against `/api/tags` names:

```python
names = {item.get("name") for item in payload.get("models", [])}
return model in names
```

The digest model id passes `smart-youtube-digest`, while Ollama-created models normally appear in tags as `smart-youtube-digest:latest`. The new benchmark and Modelfile flow also use `ollama create smart-youtube-digest`, which produces the tagged model name in normal Ollama listings. Result: `/digest-models` can mark the primary local model unavailable even after it is installed, violating the spec expectation that a missing model is shown unavailable but an installed model is available. The backend should accept both the bare name and tagged variants, at minimum `smart-youtube-digest` and `smart-youtube-digest:latest`.

### [P1] Production accepts model outputs that the quality gates say should fail

- File: `backend/app/digest.py:267`
- File: `backend/app/digest.py:343`
- Spec: `docs/specs/ollama-ai-digest.md:27`
- Spec: `docs/specs/ollama-ai-digest.md:30`
- Evidence: `docs/code-reviews/ollama-digest-benchmark-2026-05-09.md:30`

The backend silently repairs invalid agent output instead of enforcing the local model gates. Missing or invalid `source_indices` are replaced with `_nearest_chapter_index()`, and a missing or invalid `changes_summary` is replaced with a generic canned summary. That means a model response can violate the benchmark/spec requirements and still create a successful digest with potentially wrong source-image lineage.

This is not theoretical: the benchmark notes the first attempt failed because Gemma returned a text label in `source_indices` and omitted `changes_summary`. The current production normalizer would hide both failures. For the Ollama provider, invalid `source_indices` and missing `changes_summary` should fail the request clearly, or the benchmark should be redefined to allow repair and then verify repaired lineage explicitly.

### [P2] Benchmark image-preservation gate is tautological

- File: `tools/benchmark_digest_model.py:234`
- Spec: `docs/specs/ollama-ai-digest.md:31`

`score_digest()` sets:

```python
expected_images = count_source_images([source_chapters[index] for index in sorted(set(used_indices))])
preserved_images = expected_images
```

The reported `images=N/N` result cannot fail because the benchmark never inspects actual backend-normalized digest chapters or a generated digest archive. This weakens the main operational proof for the local model replacement: a benchmark pass does not prove that image references are preserved by the implementation under review. The benchmark should run the same normalization path as production or generate a temporary digest artifact and count the actual `images` fields.

### [P2] Missing-model and Ollama HTTP failures lose the useful error body

- File: `backend/app/digest.py:300`
- Spec: `docs/specs/ai-digest-version.md:35`

`_call_ollama_agent()` catches every exception and formats only the exception string. For Ollama HTTP failures, especially missing model responses, the user is likely to see a generic message such as `HTTP Error 404: Not Found` rather than the Ollama body that explains which model is missing or should be pulled/created. Since the spec requires local Ollama model failures to fail clearly, HTTP errors should be handled separately and include the response body when available. A preflight model availability check before the expensive chat call would make this clearer too.

### [P2] Local digest generation blocks the FastAPI event loop for up to 180 seconds

- File: `backend/app/main.py:195`
- File: `backend/app/digest.py:278`

`create_ai_digest()` is an async route, but it directly calls synchronous `create_digest_version()`, which performs a blocking `urllib.request.urlopen()` to local Ollama with a 180 second timeout. Local model inference can be CPU/GPU-bound and slow; while it runs, the server event loop can be unavailable for unrelated requests such as polling, reader loads, or dashboard interactions. This was already a risk with synchronous provider calls, but the local Ollama replacement makes it more operationally visible. The digest request should run in a worker/thread, background job, or other non-blocking execution path.

## Open Questions

- Should production fail strictly on any invalid Ollama JSON shape, matching the benchmark, or should it repair output and record a degraded `digest_agent_status`?
- Should `/digest-models` expose an Ollama-specific unavailable reason so the UI can say `model missing` or `Ollama unavailable` instead of provider-key language?

## Verification

- Reviewed uncommitted changes in `backend/app/digest.py`, `backend/app/main.py`, `backend/modelfiles/smart-youtube-digest.Modelfile`, `tools/benchmark_digest_model.py`, and related specs/playground docs.
- `python3 -m py_compile backend/app/digest.py backend/app/main.py tools/benchmark_digest_model.py` passed.
- `git diff --check` passed for the reviewed backend/spec files.
- Did not run the Ollama benchmark locally in this review pass.
