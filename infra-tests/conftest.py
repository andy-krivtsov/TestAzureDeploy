import pytest

def pytest_addoption(parser: pytest.Parser):
    parser.addoption("--app-urls", dest="app_urls", type=str, default="http://localhost:8000,http://localhost:8100,http://localhost:8200")
    parser.addoption("--commit", dest="commit", type=str, default="demo-commit-sha")



def pytest_generate_tests(metafunc: pytest.Metafunc):
    if "app_url" in metafunc.fixturenames:
        values = [ s.strip() for s in str(metafunc.config.getoption("app_urls")).split(',') ]
        metafunc.parametrize("app_url", values)
