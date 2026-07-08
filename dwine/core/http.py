"""HTTP layer: retrying session, checksum-verified downloads, download pool."""

from __future__ import annotations

import hashlib
import shutil
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Iterable

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .. import USER_AGENT
from .events import bus

_session: requests.Session | None = None


def session() -> requests.Session:
    global _session
    if _session is None:
        s = requests.Session()
        s.headers["User-Agent"] = USER_AGENT
        retry = Retry(
            total=4,
            backoff_factor=1.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET", "HEAD"),
        )
        adapter = HTTPAdapter(max_retries=retry, pool_maxsize=16)
        s.mount("https://", adapter)
        s.mount("http://", adapter)
        _session = s
    return _session


def get_json(url: str, timeout: int = 30, **kwargs: Any) -> Any:
    resp = session().get(url, timeout=timeout, **kwargs)
    resp.raise_for_status()
    return resp.json()


class ChecksumError(RuntimeError):
    pass


def _verify(path: Path, sha1: str | None, sha512: str | None) -> None:
    if not sha1 and not sha512:
        return
    algo, expected = ("sha512", sha512) if sha512 else ("sha1", sha1)
    digest = hashlib.new(algo)
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    actual = digest.hexdigest()
    if actual.lower() != (expected or "").lower():
        raise ChecksumError(f"{path.name}: expected {algo} {expected}, got {actual}")


def download(
    url: str,
    dest: Path,
    sha1: str | None = None,
    sha512: str | None = None,
    size: int | None = None,
    force: bool = False,
) -> Path:
    """Download ``url`` to ``dest`` atomically, skipping if already valid."""
    dest = Path(dest)
    if dest.exists() and not force:
        try:
            _verify(dest, sha1, sha512)
            return dest
        except ChecksumError:
            pass  # re-download
    dest.parent.mkdir(parents=True, exist_ok=True)
    with session().get(url, stream=True, timeout=60) as resp:
        resp.raise_for_status()
        total = size or int(resp.headers.get("Content-Length") or 0)
        done = 0
        fd = tempfile.NamedTemporaryFile(dir=str(dest.parent), delete=False)
        try:
            with fd:
                for chunk in resp.iter_content(chunk_size=1 << 16):
                    fd.write(chunk)
                    done += len(chunk)
                    bus.emit(
                        "download.progress",
                        {"url": url, "done": done, "total": total},
                    )
            tmp_path = Path(fd.name)
            _verify(tmp_path, sha1, sha512)
            shutil.move(str(tmp_path), str(dest))
        except BaseException:
            Path(fd.name).unlink(missing_ok=True)
            raise
    return dest


def download_many(
    jobs: Iterable[dict[str, Any]],
    workers: int = 8,
) -> list[Path]:
    """Parallel downloads. Each job is kwargs for :func:`download`."""
    results: list[Path] = []
    errors: list[Exception] = []
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futures = [pool.submit(download, **job) for job in jobs]
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)
    if errors:
        raise errors[0]
    return results
