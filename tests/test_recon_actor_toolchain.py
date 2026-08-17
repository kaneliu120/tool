from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRAST = ROOT / ".cursor" / "skills" / "website-page-research" / "scripts" / "http_contrast.sh"
PROBE = ROOT / ".cursor" / "skills" / "website-page-research" / "scripts" / "playwright_page_probe.py"
VENV_PY = ROOT / ".venv" / "bin" / "python"
EXAMPLE = "https://example.com/"


def test_http_contrast_example_com() -> None:
    proc = subprocess.run(
        ["bash", str(CONTRAST), EXAMPLE],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
    assert lines[0].startswith("url\t"), proc.stdout
    labels = {ln.split("\t", 1)[0] for ln in lines[1:]}
    assert "python-requests-like" in labels
    assert "curl" in labels
    assert "chrome-ua" in labels
    for ln in lines[1:]:
        parts = ln.split("\t")
        assert len(parts) >= 2
        assert parts[1] in {"200", "301", "302", "308"}, ln


def test_playwright_probe_example_com() -> None:
    assert VENV_PY.is_file()
    proc = subprocess.run(
        [str(VENV_PY), str(PROBE), "--url", EXAMPLE, "--js", "generic"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=90,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout)
    assert "error" not in payload or not payload.get("error"), payload
    assert "example.com" in str(payload.get("url") or "")
    assert payload.get("title") or payload.get("h1")


def test_check_recon_actor_env_script() -> None:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_recon_actor_env.py")],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=40,
    )
    report = json.loads(proc.stdout)
    assert report["ok"] is True, report
    assert report["errors"] == []
    assert report["cloud_playwright_probe"] is True
    assert report["mac_chrome_bridge"] is False


def test_pull_actor_worker_peers_script_exists() -> None:
    path = ROOT / "scripts" / "pull_actor_worker_peers.py"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "Apify Actors" in text
    assert "google run worker" in text
    assert "build-source-location" in text
    assert "recover_shared" in text


def test_recover_shared_from_worker_copies(tmp_path: Path) -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "pull_actor_worker_peers", ROOT / "scripts" / "pull_actor_worker_peers.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    donor = tmp_path / "airbnb-com" / "src"
    donor.mkdir(parents=True)
    for name in mod.SHARED_FILES:
        (donor / name).write_text(f"# {name}\n", encoding="utf-8")
    dest = tmp_path / "new-com"
    (dest / "src").mkdir(parents=True)
    report = mod.recover_shared(tmp_path)
    assert report["ok"] is True
    assert report["donor"] == "airbnb-com"
    script = tmp_path / "_shared" / "sync_shared.sh"
    assert script.is_file()
    proc = subprocess.run(
        ["bash", str(script), "new-com"],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert (dest / "src" / "egress_control_client.py").is_file()


def test_actor_skill_gates_exist() -> None:
    skill = ROOT / ".cursor" / "skills" / "apify-actor-cloud-run-development"
    for rel in (
        "scripts/assert_cwd.sh",
        "scripts/worker_triple_smoke.sh",
        "scripts/random_smoke_input.py",
        "templates/worker-contract.md",
    ):
        assert (skill / rel).is_file(), rel
    help_proc = subprocess.run(
        [sys.executable, str(skill / "scripts" / "random_smoke_input.py"), "--help"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert help_proc.returncode == 0, help_proc.stdout + help_proc.stderr
    assert "--matrix" in help_proc.stdout or "--out" in help_proc.stdout
