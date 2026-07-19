"""CLI entry: probe REA and record Kasada challenge artifacts."""

from __future__ import annotations

import argparse
import asyncio
import json

from rea_unblocker.recorder.challenge import KasadaRecorder


DEFAULT_URL = "https://www.realestate.com.au/buy/in-melbourne,+vic/list-1"


async def _run(url: str, artifact_dir: str) -> int:
    recorder = KasadaRecorder(artifact_dir)
    record = await recorder.probe(url)
    print(json.dumps(record.to_dict(), indent=2))
    # Probe success means we *recorded* the challenge; Argonaut means unblock worked.
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="REA Kasada challenge probe/recorder")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--artifact-dir", default="artifacts/kasada")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(_run(args.url, args.artifact_dir)))


if __name__ == "__main__":
    main()
