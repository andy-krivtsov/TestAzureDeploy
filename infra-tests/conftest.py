import pytest

def pytest_addoption(parser: pytest.Parser):
    parser.addoption("--front-url", dest="front_url", type=str, default="http://localhost:8000")
    parser.addoption("--backdb-url", dest="backdb_url", type=str, default="http://localhost:8100")
    parser.addoption("--backstor-url", dest="backstor_url", type=str, default="http://localhost:8200")
    parser.addoption("--commit", dest="commit", type=str, default="demo-commit-sha")



