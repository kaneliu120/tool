"""Kasada challenge recorder — Phase 1 asset for token-flow research."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx

from rea_unblocker.classifier.html import classify_html

IPS_RE = re.compile(
    r"""src=["']([^"']*ips\.js[^"']*)["']""",
    re.IGNORECASE,
)


@dataclass
class ChallengeRecord:
    target: str
    url: str
    capturedAt: str
    initialStatus: int | None
    bytes: int
    classification: dict[str, Any]
    responseHeaders: dict[str, str]
    cookies: dict[str, str]
    ipsPath: str | None = None
    ipsHash: str | None = None
    hasCt: bool = False
    hasCd: bool = False
    htmlSamplePath: str | None = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class KasadaRecorder:
    def __init__(self, artifact_dir: str | Path = "artifacts/kasada") -> None:
        self.artifact_dir = Path(artifact_dir)
        self.artifact_dir.mkdir(parents=True, exist_ok=True)

    async def probe(
        self,
        url: str,
        *,
        target: str = "realestate.com.au",
        user_agent: str | None = None,
        fetch_ips: bool = True,
    ) -> ChallengeRecord:
        ua = user_agent or (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        headers = {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-AU,en;q=0.9",
        }
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            resp = await client.get(url, headers=headers)
            html = resp.text
            classification = classify_html(html)
            header_map = {k.lower(): v for k, v in resp.headers.items()}
            cookies = dict(resp.cookies)
            ips_path = None
            ips_hash = None
            notes: list[str] = []

            m = IPS_RE.search(html)
            if m:
                ips_path = m.group(1)
                if fetch_ips:
                    ips_url = urljoin(str(resp.url), ips_path)
                    try:
                        ips_resp = await client.get(ips_url, headers=headers)
                        ips_hash = "sha256:" + hashlib.sha256(ips_resp.content).hexdigest()
                        ips_file = self.artifact_dir / f"ips_{ips_hash[7:19]}.js"
                        ips_file.write_bytes(ips_resp.content)
                        notes.append(f"saved ips.js -> {ips_file}")
                    except httpx.HTTPError as exc:
                        notes.append(f"ips.js fetch failed: {exc}")

            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            host = urlparse(url).hostname or "unknown"
            html_path = self.artifact_dir / f"{host}_{stamp}.html"
            html_path.write_text(html, encoding="utf-8")

            record = ChallengeRecord(
                target=target,
                url=url,
                capturedAt=datetime.now(timezone.utc).isoformat(),
                initialStatus=resp.status_code,
                bytes=classification["bytes"],
                classification=classification,
                responseHeaders={
                    k: header_map[k]
                    for k in (
                        "x-kpsdk-ct",
                        "x-kpsdk-cd",
                        "x-kpsdk-st",
                        "x-kpsdk-r",
                        "content-type",
                        "content-length",
                    )
                    if k in header_map
                },
                cookies={k: v for k, v in cookies.items() if "KP_" in k or "kpsdk" in k.lower()},
                ipsPath=ips_path,
                ipsHash=ips_hash,
                hasCt="x-kpsdk-ct" in header_map or any("KP_UID" in k for k in cookies),
                hasCd="x-kpsdk-cd" in header_map,
                htmlSamplePath=str(html_path),
                notes=notes,
            )
            out = self.artifact_dir / f"record_{stamp}.json"
            out.write_text(json.dumps(record.to_dict(), indent=2), encoding="utf-8")
            record.notes.append(f"saved record -> {out}")
            return record
