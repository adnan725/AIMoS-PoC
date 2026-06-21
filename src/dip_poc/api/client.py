from __future__ import annotations

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Iterator

import httpx

from ..config import Settings, settings as default_settings
from ..observability import api_request, api_response, api_retry, timed
from .models import Person, PersonListResponse

logger = logging.getLogger(__name__)


class DIPClient:
    def __init__(self, settings: Settings | None = None, client: httpx.Client | None = None):
        self._settings = settings or default_settings
        self._owns_client = client is None
        self._client = client or httpx.Client(
            base_url=self._settings.dip_base_url,
            timeout=self._settings.request_timeout,
            headers={"Authorization": f"ApiKey {self._settings.dip_api_key}"},
        )
        if self._settings.cache_enabled:
            self._settings.cache_dir.mkdir(parents=True, exist_ok=True)

    # lifecycle
    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "DIPClient":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()

    # caching
    def _cache_path(self, path: str, params: dict) -> Path:
        key_src = path + json.dumps(params, sort_keys=True)
        digest = hashlib.sha256(key_src.encode()).hexdigest()[:16]
        return self._settings.cache_dir / f"{digest}.json"

    # core request with retry
    def _get(self, path: str, params: dict, *, max_retries: int = 4) -> dict:
        # API key travels as a header; never cache it into the key material.
        cache_file = self._cache_path(path, params) if self._settings.cache_enabled else None
        if cache_file and cache_file.exists():
            api_request(path, params, cache_hit=True)
            return json.loads(cache_file.read_text(encoding="utf-8"))

        api_request(path, params, cache_hit=False)
        delay = 1.0
        last_exc: Exception | None = None
        for attempt in range(1, max_retries + 1):
            try:
                with timed("dip_request") as t:
                    resp = self._client.get(path, params=params)
                api_response(path, resp.status_code, t["duration_ms"], attempt)
                if resp.status_code == 429 or resp.status_code >= 500:
                    raise httpx.HTTPStatusError(
                        f"transient {resp.status_code}", request=resp.request, response=resp
                    )
                resp.raise_for_status()
                data = resp.json()
                if cache_file:
                    cache_file.write_text(
                        json.dumps(data, ensure_ascii=False), encoding="utf-8"
                    )
                return data
            except (httpx.HTTPStatusError, httpx.TransportError) as exc:
                last_exc = exc
                if attempt == max_retries:
                    break
                api_retry(path, attempt, reason=type(exc).__name__, backoff_s=delay)
                time.sleep(delay)
                delay *= 2
        raise RuntimeError(f"DIP request to {path} failed after {max_retries} attempts") from last_exc

    # public API
    def iter_persons(self, wahlperiode: int, *, page_size: int = 100) -> Iterator[Person]:
        """Yield every person of a Wahlperiode, transparently paginating.

        Termination: the DIP API echoes back the *same* cursor on the final
        page, so we stop as soon as the cursor stops changing.
        """
        params: dict = {"f.wahlperiode": wahlperiode, "format": "json"}
        cursor: str | None = None
        seen = 0
        while True:
            page_params = dict(params)
            if cursor:
                page_params["cursor"] = cursor
            page = PersonListResponse.model_validate(self._get("person", page_params))
            for person in page.documents:
                yield person
            seen += len(page.documents)
            if not page.documents or page.cursor in (None, cursor):
                break
            cursor = page.cursor
            if seen >= page.num_found:
                break

    def get_person_by_name(self, name: str, wahlperiode: int | None = None) -> list[Person]:
        """Full-text person lookup used by the 'Wer ist ...?' tool."""
        params: dict = {"f.person": name, "format": "json"}
        if wahlperiode is not None:
            params["f.wahlperiode"] = wahlperiode
        page = PersonListResponse.model_validate(self._get("person", params))
        return page.documents
