import io
import json
import os
import zipfile
import logging
from pathlib import Path

import requests
from packaging.version import Version

from cofmupy.api.version import API_VERSION

# ─────────────────────────────
# Configuration
# ─────────────────────────────

FRONTEND_REPO = "jfasquel31450/CoFmuPy-GUI"
GITHUB_API = f"https://api.github.com/repos/{FRONTEND_REPO}/releases"
DIST_DIR = Path("web/dist/cofmupy-gui")
CACHE_DIR = Path.home() / ".my-app" / "frontend-cache"
TIMEOUT = 10

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("gui-fetcher")


# ─────────────────────────────
# Helpers
# ─────────────────────────────

def github_headers():
    token = os.getenv("GITHUB_TOKEN")
    if token:
        return {"Authorization": f"token {token}"}
    return {}


def api_range_contains(api_version: Version, min_v: str, max_v: str) -> bool:
    min_v = Version(min_v)
    if max_v.endswith(".x"):
        max_v = Version(max_v.replace(".x", ".999"))
    else:
        max_v = Version(max_v)

    return min_v <= api_version <= max_v


def is_compatible(meta: dict) -> bool:
    compat = meta.get("api_compatibility", {})
    return api_range_contains(
        API_VERSION,
        compat["min"],
        compat["max"]
    )


# ─────────────────────────────
# Core logic
# ─────────────────────────────

def fetch_frontend():
    log.info("Backend API version: %s", API_VERSION)

    r = requests.get(GITHUB_API, headers=github_headers(), timeout=TIMEOUT)
    r.raise_for_status()

    releases = r.json()

    for release in releases:
        assets = {a["name"]: a for a in release["assets"]}

        if "metadata-dist.json" not in assets:
            continue
        if "CoFmuPy-gui-dist.zip" not in assets:
            continue

        meta_url = assets["metadata-dist.json"]["browser_download_url"]
        meta = requests.get(meta_url, timeout=TIMEOUT).json()

        if not is_compatible(meta):
            continue

        tag = release["tag_name"]
        log.info("Compatible frontend found: %s", tag)

        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_zip = CACHE_DIR / f"{tag}.zip"

        if not cache_zip.exists():
            log.info("Downloading CoFmuPy-gui-dist.zip")
            zip_data = requests.get(
                assets["CoFmuPy-gui-dist.zip"]["browser_download_url"],
                headers=github_headers(),
                timeout=TIMEOUT
            ).content
            cache_zip.write_bytes(zip_data)
        else:
            log.info("Using cached frontend build")

        if DIST_DIR.exists():
            log.info("Cleaning existing dist directory")
            for item in DIST_DIR.iterdir():
                if item.is_dir():
                    os.system(f"rm -rf {item}")
                else:
                    item.unlink()

        DIST_DIR.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(cache_zip) as z:
            z.extractall(DIST_DIR)

        log.info("Frontend installed in %s", DIST_DIR)
        return

    raise RuntimeError("No compatible frontend found for API version")


# ─────────────────────────────
# CLI entrypoint
# ─────────────────────────────

def main():
    try:
        fetch_frontend()
    except Exception as e:
        log.error("Failed to fetch frontend: %s", e)
        raise SystemExit(1)
