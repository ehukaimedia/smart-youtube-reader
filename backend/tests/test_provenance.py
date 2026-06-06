import json

from app import digest, intelligence, pipeline
from app.jobs import Job
from app.schemas import JobCreateRequest


def test_archive_provenance_records_runtime_and_prompt_contract(monkeypatch):
    monkeypatch.setattr(
        intelligence,
        "app_metadata",
        lambda: {"name": "smart-youtube-reader", "commit": "test-sha"},
    )
    monkeypatch.setattr(
        intelligence,
        "runtime_metadata",
        lambda model: {
            "provider": "ollama",
            "model": model,
            "host": "http://127.0.0.1:11434",
            "capabilities": ["text", "image"],
            "installed": True,
        },
    )

    provenance = intelligence._archive_provenance("gemma4:12b")

    assert provenance["schema_version"] == 1
    assert provenance["app"]["commit"] == "test-sha"
    assert provenance["runtime"]["provider"] == "ollama"
    assert provenance["runtime"]["model"] == "gemma4:12b"
    assert provenance["generation"]["archive_prompt_version"] == "archive-xml-v1"
    assert provenance["generation"]["vision_prompt_version"] == "vision-frame-selection-v1"


def test_archive_frame_paths_are_portable_for_windows_and_posix_inputs():
    assert pipeline._archive_frame_path("0001.png") == "frames/0001.png"
    assert pipeline._archive_frame_path("frames/0002.png") == "frames/0002.png"
    assert pipeline._archive_frame_path(r"C:\tmp\frames\0003.png") == "frames/0003.png"

    selection = pipeline._relativize_image_selection_paths({
        "selected_images": ["0001.png", r"C:\tmp\frames\0002.png"],
        "candidates": [
            {"filename": "0001.png", "timestamp": 0.0},
            {"filename": r"C:\tmp\frames\0002.png", "timestamp": 15.0},
        ],
    })

    assert selection["selected_images"] == ["frames/0001.png", "frames/0002.png"]
    assert selection["candidates"][0]["filename"] == "frames/0001.png"
    assert selection["candidates"][1]["filename"] == "frames/0002.png"
    assert "\\" not in json.dumps(selection)


def test_job_response_refreshes_model_from_manifest(tmp_path):
    job = Job("job-1", JobCreateRequest(video_url="https://youtu.be/example"))
    job.data_dir = tmp_path
    (tmp_path / "manifest.json").write_text(
        json.dumps({
            "job_id": "job-1",
            "url": "https://youtu.be/example",
            "title": "Example",
            "model": "gemma4:26b",
            "status": "complete",
        }),
        encoding="utf-8",
    )

    response = job.to_response()

    assert response.model == "gemma4:26b"


def test_external_agent_digest_separates_source_and_digest_provenance(tmp_path, monkeypatch):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    source_provenance = {
        "schema_version": 1,
        "runtime": {"provider": "ollama", "model": "gemma4:12b"},
    }
    source_chapters = [
        {
            "concept": f"Source Chapter {index}",
            "summary": "Useful source summary.",
            "content": "Specific durable lesson with enough evidence and concrete detail. " * 6,
            "timestamp_start": index * 60,
            "timestamp_end": index * 60 + 55,
            "images": [f"frames/{index:04d}.png"],
        }
        for index in range(4)
    ]
    (source_dir / "archive.json").write_text(
        json.dumps({
            "job_id": "source-job",
            "archive": source_chapters,
            "provenance": source_provenance,
        }),
        encoding="utf-8",
    )
    (source_dir / "manifest.json").write_text(
        json.dumps({
            "job_id": "source-job",
            "url": "https://youtu.be/example",
            "title": "Source",
            "created_at": 1,
            "model": "gemma4:12b",
            "video_ext": "mp4",
            "archive_chapters": len(source_chapters),
            "provenance": source_provenance,
        }),
        encoding="utf-8",
    )

    jobs_root = tmp_path / "jobs"
    jobs_root.mkdir()
    monkeypatch.setattr(digest, "DATA_ROOT", jobs_root)
    monkeypatch.setattr(
        digest,
        "app_metadata",
        lambda: {"name": "smart-youtube-reader", "commit": "digest-sha"},
    )
    draft = {
        "title": "Condensed Lessons",
        "chapters": [
            {
                "source_indices": [0, 1],
                "concept": "Condensed First Lesson",
                "summary": "Merged lesson.",
                "content": "Condensed evidence with named details and concrete claims. " * 7,
                "timestamp_start": 0,
                "timestamp_end": 115,
            },
            {
                "source_indices": [2, 3],
                "concept": "Condensed Second Lesson",
                "summary": "Merged lesson.",
                "content": "Condensed evidence with named details and concrete claims. " * 7,
                "timestamp_start": 120,
                "timestamp_end": 235,
            },
        ],
        "changes_summary": ["Merged source chapters.", "Removed repetition."],
    }

    digest_dir, _, manifest = digest.materialize_digest_project(source_dir, draft)
    archive = json.loads((digest_dir / "archive.json").read_text(encoding="utf-8"))

    assert manifest["provenance"]["runtime"]["provider"] == "external-agent-cli"
    assert manifest["provenance"]["app"]["commit"] == "digest-sha"
    assert manifest["model"] == "external-agent-cli"
    assert manifest["source_provenance"]["runtime"]["model"] == "gemma4:12b"
    assert archive["provenance"]["runtime"]["provider"] == "external-agent-cli"
    assert archive["source_provenance"]["runtime"]["model"] == "gemma4:12b"
