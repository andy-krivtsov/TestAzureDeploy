from enum import Enum
import pytest
import urllib3
import logging

retries = urllib3.Retry(connect=5, read=3, redirect=3, status=3)
http = urllib3.PoolManager(retries=retries)

HEALTH_PATH = "/health/live"

@pytest.fixture
def git_commit(pytestconfig: pytest.Config) -> str:
    return pytestconfig.getoption("commit")

class TestApplications:
    def test_app(self, app_url: str, git_commit :str):
        resp = http.request("GET", app_url + HEALTH_PATH)

        assert resp.status == 200

        logging.info(resp.data)

        data = resp.json()
        assert data["commit"] == git_commit

