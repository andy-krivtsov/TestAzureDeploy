from functools import wraps
from http import HTTPStatus
from azure.cosmos.exceptions import CosmosHttpResponseError
from demoapp.services.interface.repository import RepositoryAlreadyExistException, RepositoryNotFoundException, RepositoryException

def get_repository_exception(exc: CosmosHttpResponseError) -> RepositoryException:
    if exc.status_code == HTTPStatus.CONFLICT:
        return RepositoryAlreadyExistException(exc.message)
    elif exc.status_code == HTTPStatus.NOT_FOUND:
        return RepositoryNotFoundException(exc.message)
    else:
        return RepositoryException(f"{exc.status_code}: {exc.message}")

def convert_cosmosdb_exceptions(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        try:
            return f(*args, **kwds)
        except CosmosHttpResponseError as exc:
            raise get_repository_exception(exc)

    return wrapper
