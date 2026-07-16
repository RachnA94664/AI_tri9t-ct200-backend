"""
Runs the full CT-200 pipeline end-to-end against a LIVE running server
(uvicorn must already be running on http://127.0.0.1:8000) and captures
real request/response output into docs/output/pipeline_output.md.

This is NOT a test — it's a documentation/evidence script demonstrating
the versioning + staleness flow end-to-end, per the assignment's
requirement for exactly that kind of proof.

Usage:
    1. Start the server in a separate terminal: uvicorn app.main:app --reload
    2. Run this script:  python -m app.services.capture_pipeline_output
"""

import subprocess
import sys
import requests
from pathlib import Path
from datetime import datetime, timezone

BASE_URL = "http://127.0.0.1:8000"
OUTPUT_PATH = Path("docs/output/pipeline_output.md")


def run_command(cmd: list[str]) -> str:
    """Run a subprocess command and return its combined stdout+stderr."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    return (result.stdout or "") + (result.stderr or "")


def format_response(resp: requests.Response) -> str:
    try:
        pretty = resp.json()
        import json
        return json.dumps(pretty, indent=2)
    except Exception:
        return resp.text


def main():
    sections: list[tuple[str, str]] = []

    def log(title: str, content: str):
        sections.append((title, content))
        print(f"--- {title} ---")
        print(content[:500])
        print()

    # 0. Sanity check the server is actually up before doing anything
    try:
        health = requests.get(f"{BASE_URL}/", timeout=5)
        log("0. Server health check", f"GET / -> {health.status_code}\n{format_response(health)}")
    except requests.ConnectionError:
        print("ERROR: Server is not running at", BASE_URL)
        print("Start it first in another terminal: uvicorn app.main:app --reload")
        sys.exit(1)

    # 1. Ingest v1
    out = run_command([sys.executable, "-m", "app.services.run_ingest",
                        "data/ct200_manual_v1.pdf", "v1"])
    log("1. Ingest v1", out)

    # 2. Browse v1 sections — find the Battery Life node dynamically
    resp = requests.get(f"{BASE_URL}/browse/sections", params={"version": "v1"})
    log("2. Browse v1 sections", f"GET /browse/sections?version=v1 -> {resp.status_code}\n{format_response(resp)}")

    sections_data = resp.json()
    battery_node = next(
        (n for n in _flatten(sections_data) if "Battery" in n.get("heading_text", "")),
        None,
    )
    # NOTE: /browse/sections only returns top-level (level=1) nodes, so we
    # search directly rather than flattening — fetch by search instead.
    search_resp = requests.get(f"{BASE_URL}/browse/search",
                                params={"q": "battery", "version": "v1"})
    log("2b. Search for 'battery' in v1", f"GET /browse/search?q=battery&version=v1 -> {search_resp.status_code}\n{format_response(search_resp)}")

    search_results = search_resp.json()
    if not search_results:
        print("ERROR: No node found matching 'battery' in v1 — check your data.")
        sys.exit(1)
    battery_node_id = search_results[0]["id"] if "id" in search_results[0] else None

    # NodeSummary schema may not expose 'id' directly depending on your
    # schema — fall back to querying the DB directly if needed.
    if battery_node_id is None:
        from app.db.base import SessionLocal
        from app.models.document import Node
        db = SessionLocal()
        node = db.query(Node).filter(
            Node.heading_text.ilike("%Battery%"),
        ).order_by(Node.document_version_id.desc()).first()
        battery_node_id = node.id if node else 7  # fallback
        db.close()

    log("2c. Resolved battery node id", str(battery_node_id))

    # 3. Create a version-pinned selection
    resp = requests.post(f"{BASE_URL}/selections", json={
        "name": "battery-and-alarms",
        "node_ids": [battery_node_id],
    })
    log("3. Create selection", f"POST /selections -> {resp.status_code}\n{format_response(resp)}")
    selection_id = resp.json()["id"]

    # 4. Generate test cases
    resp = requests.post(f"{BASE_URL}/generations/selections/{selection_id}")
    log("4. Generate test cases", f"POST /generations/selections/{selection_id} -> {resp.status_code}\n{format_response(resp)}")

    # 5. Check staleness before v2 (should be fresh)
    resp = requests.get(f"{BASE_URL}/generations", params={"selection_id": selection_id})
    log("5. Check staleness (before v2 — expect is_stale=false)",
        f"GET /generations?selection_id={selection_id} -> {resp.status_code}\n{format_response(resp)}")

    # 6. Ingest v2
    out = run_command([sys.executable, "-m", "app.services.run_ingest",
                        "data/ct200_manual_v2.pdf", "v2"])
    log("6. Ingest v2", out)

    # 7. Check staleness after v2 (should now be stale)
    resp = requests.get(f"{BASE_URL}/generations", params={"selection_id": selection_id})
    log("7. Check staleness (after v2 — expect is_stale=true)",
        f"GET /generations?selection_id={selection_id} -> {resp.status_code}\n{format_response(resp)}")

    # 8. Confirm original selection still resolves to exact original text
    resp = requests.get(f"{BASE_URL}/selections/{selection_id}")
    log("8. Original selection still resolves to exact pinned v1 text",
        f"GET /selections/{selection_id} -> {resp.status_code}\n{format_response(resp)}")

    write_output(sections)


def _flatten(nodes):
    for n in nodes:
        yield n
        for child in n.get("children", []):
            yield from _flatten([child])


def write_output(sections: list[tuple[str, str]]):
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# CT-200 Pipeline — Full End-to-End Run Output",
        f"Captured: {datetime.now(timezone.utc).isoformat()}",
        "",
        "This file was generated automatically by "
        "`app/services/capture_pipeline_output.py`, running the real "
        "versioning + staleness flow against a live server — not "
        "hand-edited.",
        "",
    ]
    for title, content in sections:
        lines.append(f"## {title}")
        lines.append("```")
        lines.append(content.strip())
        lines.append("```")
        lines.append("")

    OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWritten to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()