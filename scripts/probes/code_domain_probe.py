#!/usr/bin/env python3
"""WP-K0 local fixture probe: AST L1 slices + cite-gated L2. No Mongo."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "fixtures" / "code-domain-mini"
SCHEMA_L1 = ROOT / "docs" / "schemas" / "code_l1_chunk.json"
SCHEMA_L2 = ROOT / "docs" / "schemas" / "wiki_derived_card.json"
DEFAULT_OUT = ROOT / "docs" / "probe-results" / "code_domain_k0.json"

REPO = "code-domain-mini"
EMBED_L1 = "voyage-code-3"
EMBED_L2 = "voyage-4-large"
COMMIT_V1 = "v1-fixture"
COMMIT_V2 = "v2-fixture"
TOKEN_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]{2,}\b")
STOP = {
    "the",
    "and",
    "for",
    "return",
    "def",
    "class",
    "none",
    "load",
    "before",
    "traffic",
    "build",
    "payload",
    "module",
    "function",
    "uses",
    "calls",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _required_ok(obj: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    missing = [k for k in schema.get("required", []) if k not in obj]
    return missing


def slice_py(path: Path, repo: str, commit: str, valid_from: str) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    lines = text.splitlines(keepends=True)
    file_hash = sha256_text(text)
    rel = path.name
    out: list[dict[str, Any]] = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            kind, name = "function", node.name
            start, end = node.lineno, node.end_lineno or node.lineno
        elif isinstance(node, ast.ClassDef):
            kind, name = "class", node.name
            start, end = node.lineno, node.end_lineno or node.lineno
        else:
            continue
        chunk_text = "".join(lines[start - 1 : end])
        out.append(
            {
                "kind": "code.symbol",
                "repo": repo,
                "path": rel,
                "commit_sha": commit,
                "start": start,
                "end": end,
                "sha256": file_hash,
                "symbol_name": name,
                "symbol_kind": kind,
                "language": "py",
                "text": chunk_text,
                "valid_from": valid_from,
                "valid_to": None,
                "superseded_by": None,
                "embed_model": EMBED_L1,
            }
        )
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if not isinstance(item, ast.FunctionDef):
                    continue
                m_start, m_end = item.lineno, item.end_lineno or item.lineno
                out.append(
                    {
                        "kind": "code.symbol",
                        "repo": repo,
                        "path": rel,
                        "commit_sha": commit,
                        "start": m_start,
                        "end": m_end,
                        "sha256": file_hash,
                        "symbol_name": f"{node.name}.{item.name}",
                        "symbol_kind": "method",
                        "language": "py",
                        "text": "".join(lines[m_start - 1 : m_end]),
                        "valid_from": valid_from,
                        "valid_to": None,
                        "superseded_by": None,
                        "embed_model": EMBED_L1,
                    }
                )
    return out


def current_symbols(chunks: list[dict[str, Any]]) -> set[str]:
    return {
        str(c["symbol_name"])
        for c in chunks
        if c.get("valid_to") is None and c.get("symbol_name")
    }


def invalidate_stale(
    old: list[dict[str, Any]], new: list[dict[str, Any]], when: str
) -> list[dict[str, Any]]:
    new_by = {(c["path"], c["symbol_name"]): c for c in new}
    merged = []
    for chunk in old:
        key = (chunk["path"], chunk["symbol_name"])
        nxt = new_by.get(key)
        if nxt is None or nxt["sha256"] != chunk["sha256"] or nxt["text"] != chunk["text"]:
            chunk = dict(chunk)
            chunk["valid_to"] = when
            if nxt is not None:
                chunk["superseded_by"] = f"{nxt['path']}:{nxt['start']}-{nxt['end']}"
        merged.append(chunk)
    seen = {(c["path"], c["symbol_name"], c.get("valid_to")) for c in merged}
    for chunk in new:
        key = (chunk["path"], chunk["symbol_name"], None)
        if key not in seen:
            merged.append(chunk)
    return merged


def cite_gate(card: dict[str, Any]) -> str:
    cites = card.get("cites") or []
    if not cites:
        return "reject:no_cites"
    joined = "\n".join(str(c.get("source_text") or "") for c in cites)
    names = [
        t
        for t in TOKEN_RE.findall(str(card.get("text") or ""))
        if t.lower() not in STOP and (t[:1].isupper() or "_" in t)
    ]
    missing = [t for t in names if t not in joined]
    if missing:
        return "reject:uncited:" + ",".join(missing)
    return "ok"


def template_l2(chunks: list[dict[str, Any]], commit: str) -> dict[str, Any]:
    current = [c for c in chunks if c.get("valid_to") is None]
    pick = next(c for c in current if c.get("symbol_name") == "handoff")
    text = "flow calls handoff."
    return {
        "kind": "wiki.derived",
        "layer": "flow",
        "repo": REPO,
        "commit_sha": commit,
        "cites": [
            {
                "path": pick["path"],
                "start": pick["start"],
                "end": pick["end"],
                "sha256": pick["sha256"],
                "source_text": pick["text"],
            }
        ],
        "text": text,
        "valid_from": now(),
        "valid_to": None,
        "embed_model": EMBED_L2,
    }


def ptos_card(commit: str) -> dict[str, Any]:
    return {
        "kind": "wiki.derived",
        "layer": "overview",
        "repo": REPO,
        "commit_sha": commit,
        "cites": [],
        "text": "Cache and greet orchestrate the whole platform without source spans.",
        "valid_from": now(),
        "valid_to": None,
        "embed_model": EMBED_L2,
    }


def load_schema(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run() -> dict[str, Any]:
    ts = now()
    schema_l1 = load_schema(SCHEMA_L1)
    schema_l2 = load_schema(SCHEMA_L2)
    v1_dir = FIXTURE / "v1"
    v2_dir = FIXTURE / "v2"
    v1 = []
    for py in sorted(v1_dir.glob("*.py")):
        v1.extend(slice_py(py, REPO, COMMIT_V1, ts))
    v2 = []
    for py in sorted(v2_dir.glob("*.py")):
        v2.extend(slice_py(py, REPO, COMMIT_V2, ts))
    for chunk in v1 + v2:
        missing = _required_ok(chunk, schema_l1)
        if missing:
            raise SystemExit(f"L1 schema missing {missing} in {chunk.get('symbol_name')}")
    merged = invalidate_stale(v1, v2, ts)
    current = current_symbols(merged)
    l2 = template_l2(merged, COMMIT_V2)
    if _required_ok(l2, schema_l2):
        raise SystemExit(f"L2 schema missing {_required_ok(l2, schema_l2)}")
    l2_gate = cite_gate(l2)
    ptos = ptos_card(COMMIT_V2)
    ptos_gate = cite_gate(ptos)
    report = {
        "v1_symbols": sorted(current_symbols(v1)),
        "v2_current_symbols": sorted(current),
        "old_greet_still_current": "greet" in current,
        "l2_gate": l2_gate,
        "ptos_gate": ptos_gate,
        "ptos_reject_rate": 1.0 if ptos_gate.startswith("reject") else 0.0,
        "l1_count_v1": len(v1),
        "l1_count_merged": len(merged),
        "embed_model_l1": EMBED_L1,
        "embed_model_l2": EMBED_L2,
    }
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()
    report = run()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    if report["old_greet_still_current"]:
        return 1
    if report["l2_gate"] != "ok":
        return 1
    if report["ptos_reject_rate"] != 1.0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
