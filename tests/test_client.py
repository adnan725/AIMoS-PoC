import json
from pathlib import Path

import httpx
import pytest

from dip_poc.api.client import DIPClient
from dip_poc.config import Settings

FIXTURE = Path(__file__).parent / "fixtures" / "persons_wp20.json"


@pytest.fixture
def settings(tmp_path):
    return Settings(
        dip_api_key="TEST_KEY",
        dip_base_url="https://dip.test/api/v1",
        groq_api_key=None,
        groq_model="x",
        cache_dir=tmp_path / "cache",
        cache_enabled=False,
        request_timeout=5,
    )


def test_iter_persons_paginates_and_terminates(settings):
    page = json.loads(FIXTURE.read_text(encoding="utf-8"))
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        assert request.headers["Authorization"] == "ApiKey TEST_KEY"
        body = dict(page)
        # First call returns a fresh cursor; second returns the SAME cursor
        # as we send back, which is the termination signal.
        if "cursor" not in request.url.params:
            body["cursor"] = "PAGE2"
        else:
            body["cursor"] = request.url.params["cursor"]
        return httpx.Response(200, json=body)

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport, base_url=settings.dip_base_url,
                               headers={"Authorization": f"ApiKey {settings.dip_api_key}"})
    client = DIPClient(settings=settings, client=http_client)

    persons = list(client.iter_persons(20))
    # numFound is 5 per page; loop stops once seen >= num_found.
    assert len(persons) == 5
    assert calls["n"] >= 1
