"""Fetch source files from public GitHub at a given commit.

The dataset stores metadata only (repo, commit SHA, file path). The actual
source is pulled at run time from raw.githubusercontent.com and cached under
.cache/ so a reviewer can reproduce without us vendoring third-party code of
mixed licenses.

Only public, read-only GitHub raw URLs are used. No authentication, no writes.
"""

from __future__ import annotations

import hashlib
import os
import urllib.request
from pathlib import Path

CACHE_DIR = Path(os.environ.get("LAB_CACHE", ".cache"))


class FetchError(RuntimeError):
    pass


def _raw_url(repo: str, sha: str, path: str) -> str:
    # repo is "owner/name"
    return f"https://raw.githubusercontent.com/{repo}/{sha}/{path}"


def fetch_file(repo: str, sha: str, path: str, timeout: int = 30) -> str:
    url = _raw_url(repo, sha, path)
    key = hashlib.sha256(url.encode()).hexdigest()[:16]
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cached = CACHE_DIR / f"{key}.txt"
    if cached.exists():
        return cached.read_text(encoding="utf-8", errors="replace")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "agent-security-lab"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
    except Exception as exc:  # noqa: BLE001
        raise FetchError(f"could not fetch {url}: {exc}") from exc
    cached.write_text(body, encoding="utf-8")
    return body
