"""Shared helpers: config loading, project paths, JSON IO."""
import json
import os
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
FONTS = SKILL_DIR / "fonts"


def load_env():
    """Load KEY=VALUE pairs from .env (skill dir, then current dir). Real env vars win."""
    for p in (SKILL_DIR / ".env", Path.cwd() / ".env"):
        if p.exists():
            for line in p.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_env()


def env(name, default=None, required=False):
    v = os.environ.get(name, default)
    if required and not v:
        sys.exit(f"Missing config: {name}. Add it to .env (see .env.example).")
    return v


def read_json(path, default=None):
    path = Path(path)
    if not path.exists():
        if default is not None:
            return default
        sys.exit(f"{path} not found.")
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, data):
    tmp = Path(path).with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(path)


def project(project_dir):
    root = Path(project_dir).resolve()
    if not (root / "comic.json").exists():
        sys.exit(f"{root / 'comic.json'} not found.")
    d = {"root": root, "comic": root / "comic.json", "img": root / "img", "proof": root / "proof", "out": root / "out"}
    for k in ("img", "proof", "out"):
        d[k].mkdir(parents=True, exist_ok=True)
    return d
