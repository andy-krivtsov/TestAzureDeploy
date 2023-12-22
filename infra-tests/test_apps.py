from enum import Enum
import pytest
import urllib3

retries = urllib3.Retry(connect=5, read=3, redirect=3, status=3)
http = urllib3.PoolManager(retries=retries)

HEALTH_PATH = "/health/live"

class AppEnum(str, Enum):
    front = "front"
    backdb = "backdb"
    backstor = "backstor"

@pytest.fixture
def app_urls(pytestconfig: pytest.Config) -> dict:
    return {
        AppEnum.front: pytestconfig.getoption("front_url"),
        AppEnum.backdb: pytestconfig.getoption("backdb_url"),
        AppEnum.backstor: pytestconfig.getoption("backstor_url"),
    }

@pytest.fixture
def git_commit(pytestconfig: pytest.Config) -> str:
    return pytestconfig.getoption("commit")

class TestApplications:
    def _test_app(self, url: str, git_commit :str):
        resp = http.request("GET", url + HEALTH_PATH)

        assert resp.status == 200

        data = resp.json()
        assert data["commit"] == git_commit


    def test_front(self, app_urls: dict, git_commit: str):
        self._test_app(app_urls[AppEnum.front], git_commit)

    def test_backdb(self, app_urls: dict, git_commit: str):
        self._test_app(app_urls[AppEnum.backdb], git_commit)

    def test_backstor(self, app_urls: dict, git_commit: str):
        self._test_app(app_urls[AppEnum.backstor], git_commit)

