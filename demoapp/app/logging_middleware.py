import logging
import json
from typing import Awaitable, Callable
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware


async def log_options_requests(request: Request, call_next: Callable) -> Response:
    if request.method == "OPTIONS":
        headers = dict(request.headers)
        logging.info("Request log: URL: %s", request.url)
        logging.info("Request log: headers: %s", json.dumps(headers, indent=2))

    response: Response = await call_next(request)

    if request.method == "OPTIONS":
        headers = dict(response.headers)
        logging.info("Response log: headers: %s", json.dumps(headers, indent=2))

    return response
