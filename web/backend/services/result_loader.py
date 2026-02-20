"""Result loading service — wraps bench.visualize.load_all_results()."""

import json
import os

from ..config import RESULTS_DIR


def load_all_results(results_dir: str | None = None) -> dict[str, dict]:
    """Load all framework result JSONs from disk."""
    rdir = results_dir or RESULTS_DIR
    data = {}
    for fw in ["sglang", "vllm", "ollama"]:
        fw_dir = os.path.join(rdir, fw)
        if not os.path.isdir(fw_dir):
            continue
        for fname in sorted(os.listdir(fw_dir)):
            if fname.endswith("_results.json"):
                fpath = os.path.join(fw_dir, fname)
                with open(fpath) as f:
                    data[fw] = json.load(f)
                break
    return data


def list_result_files() -> dict[str, list[str]]:
    """List result files per framework."""
    out: dict[str, list[str]] = {}
    for fw in ["sglang", "vllm", "ollama"]:
        fw_dir = os.path.join(RESULTS_DIR, fw)
        if not os.path.isdir(fw_dir):
            continue
        files = [f for f in sorted(os.listdir(fw_dir)) if f.endswith(".json")]
        if files:
            out[fw] = files
    return out


def load_framework_results(framework: str) -> dict | None:
    """Load results for a specific framework."""
    fw_dir = os.path.join(RESULTS_DIR, framework)
    if not os.path.isdir(fw_dir):
        return None
    for fname in sorted(os.listdir(fw_dir)):
        if fname.endswith("_results.json"):
            with open(os.path.join(fw_dir, fname)) as f:
                return json.load(f)
    return None


def clear_all_results() -> dict[str, int]:
    """Delete all result JSON files. Returns count of deleted files per framework."""
    deleted: dict[str, int] = {}
    for fw in ["sglang", "vllm", "ollama"]:
        fw_dir = os.path.join(RESULTS_DIR, fw)
        if not os.path.isdir(fw_dir):
            continue
        count = 0
        for fname in os.listdir(fw_dir):
            if fname.endswith(".json"):
                os.remove(os.path.join(fw_dir, fname))
                count += 1
        if count:
            deleted[fw] = count
    # Also clear summary dir
    summary_dir = os.path.join(RESULTS_DIR, "summary")
    if os.path.isdir(summary_dir):
        import shutil
        shutil.rmtree(summary_dir, ignore_errors=True)
    return deleted


def clear_framework_results(framework: str) -> int:
    """Delete result JSON files for a specific framework. Returns count of deleted files."""
    fw_dir = os.path.join(RESULTS_DIR, framework)
    if not os.path.isdir(fw_dir):
        return 0
    count = 0
    for fname in os.listdir(fw_dir):
        if fname.endswith(".json"):
            os.remove(os.path.join(fw_dir, fname))
            count += 1
    return count
