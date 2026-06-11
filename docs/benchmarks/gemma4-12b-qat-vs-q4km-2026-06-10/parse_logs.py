#!/usr/bin/env python3
"""Rebuild summary.json from the raw benchmark logs in this directory.

Usage:
    backend\\.venv\\Scripts\\python.exe docs\\benchmarks\\gemma4-12b-qat-vs-q4km-2026-06-10\\parse_logs.py

The raw logs are stdout captures of backend/benchmark_model.py; this script
extracts the per-call JSON rows and image-selection rows and aggregates them.
"""

from __future__ import annotations

import json
from pathlib import Path

DIR = Path(__file__).resolve().parent

FILES = {
    ("baseline", "sample"): "baseline-sample.txt",
    ("baseline", "teded"): "baseline-teded.txt",
    ("baseline", "trading"): "baseline-trading.txt",
    ("baseline", "trading_run2"): "baseline-trading-run2.txt",
    ("qat", "sample"): "qat-sample.txt",
    ("qat", "teded"): "qat-teded.txt",
    ("qat", "trading"): "qat-trading.txt",
    ("qat", "trading_run2"): "qat-trading-run2.txt",
}


def json_blocks(text: str):
    """Yield top-level JSON objects printed sequentially in the log."""
    depth = 0
    start = None
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                try:
                    yield json.loads(text[start : i + 1])
                except json.JSONDecodeError:
                    pass
                start = None


def main() -> None:
    out: dict = {}
    for (model, suite), fname in FILES.items():
        text = (DIR / fname).read_text(encoding="utf-8", errors="replace")
        rows = [b for b in json_blocks(text) if "format" in b and "quality" in b and "run" in b]
        img_rows = [b for b in json_blocks(text) if "selected" in b and "selection" in b]
        per_format = {}
        for fmt in ("schema_json", "json", "xml"):
            frows = [r for r in rows if r.get("format") == fmt]
            if not frows:
                continue
            secs = [float(r.get("seconds", 0)) for r in frows]
            quals = [int(r.get("quality", 0)) for r in frows]
            per_format[fmt] = {
                "calls": len(frows),
                "passed": sum(1 for q in quals if q == 7),
                "avg_quality": round(sum(quals) / len(quals), 2),
                "min_quality": min(quals),
                "avg_seconds": round(sum(secs) / len(secs), 2),
                "total_seconds": round(sum(secs), 1),
                "errors": sum(1 for r in frows if r.get("error")),
            }
        all_secs = [float(r.get("seconds", 0)) for r in rows]
        all_quals = [int(r.get("quality", 0)) for r in rows]
        suite_summary = {
            "calls": len(rows),
            "passed": sum(1 for q in all_quals if q == 7),
            "pass_rate": round(sum(1 for q in all_quals if q == 7) / len(rows), 3) if rows else 0,
            "avg_quality": round(sum(all_quals) / len(all_quals), 2) if rows else 0,
            "avg_seconds_per_call": round(sum(all_secs) / len(all_secs), 2) if rows else 0,
            "total_seconds": round(sum(all_secs), 1),
            "errors": sum(1 for r in rows if r.get("error")),
            "per_format": per_format,
        }
        if img_rows:
            methods: dict = {}
            for r in img_rows:
                m = r["selection"].get("method", "?")
                methods[m] = methods.get(m, 0) + 1
            suite_summary["image_selection"] = {
                "chapters": len(img_rows),
                "methods": methods,
                "avg_visual_score": round(
                    sum(float(r.get("avg_visual_score", 0)) for r in img_rows) / len(img_rows), 3
                ),
            }
        out.setdefault(model, {})[suite] = suite_summary

    for model in out:
        total_calls = sum(s["calls"] for s in out[model].values())
        total_passed = sum(s["passed"] for s in out[model].values())
        total_secs = sum(s["total_seconds"] for s in out[model].values())
        total_errors = sum(s["errors"] for s in out[model].values())
        qsum = sum(s["avg_quality"] * s["calls"] for s in out[model].values())
        out[model]["overall_text"] = {
            "calls": total_calls,
            "passed": total_passed,
            "pass_rate": round(total_passed / total_calls, 3),
            "avg_quality": round(qsum / total_calls, 2),
            "avg_seconds_per_call": round(total_secs / total_calls, 2),
            "total_seconds": round(total_secs, 1),
            "errors": total_errors,
        }

    (DIR / "summary.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"wrote {DIR / 'summary.json'}")


if __name__ == "__main__":
    main()
