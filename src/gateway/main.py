"""
Barflow API Gateway

The gateway is the only entry point of the back end.
The sender (the front end POS, or a service) sends every request to it, and it forwards the request to
the receiver service, the one the request is meant for.

For each request under /api/v1/<service>/...:
    1. finds the service from the URL (404 if unknown);
    2. checks the token, except for the public routes (401 if invalid);
    3. removes any X-User-Id / X-User-Role sent by the client, and adds its own from the token;
    4. forwards the request unchanged to the receiver service and sends the receiver's answer back to the sender unchanged
       (503 if the service cannot be reached).

see config.py for the variable settings

Author: Zacchary Bedard-Chenier
Date: 26/11/2026
Version: 1.0
"""

import logging
import time
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request

from . import config
from .auth import AuthError, read_user
from .errors import json_error
from .proxy import forward

# console output to keep track of what the Gateway is doing
# logger contains: method, path, status and duration
# Never includes the token, the body or the query string (no personal data in the logs)
logger = logging.getLogger('gateway')
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s gateway: %(message)s')) # current date and time + logged message
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']

# Headers of the client's request that are copied to the service. Every other header is dropped,
# in particular X-User-Id and X-User-Role: only the gateway may set them.
COPIED_REQUEST_HEADERS = ('content-type', 'accept')


def create_client():
    # Creates the HTTP client shared by every request
    return httpx.AsyncClient()  # httpx waits 5 seconds by default


@asynccontextmanager
async def lifespan(app):
    # runs once, when the gateway starts
    config.get_jwt_secret() # returns a Runtime error if the secret is missing
    app.state.client = create_client()
    try:
        yield # waits until the Gateway is stopped
    finally:
        # runs once, when the gateway stops
        await app.state.client.aclose()


app = FastAPI(title='Barflow API Gateway', lifespan=lifespan)


@app.get('/')
async def root():
    return {'message': 'API is online'}


@app.api_route(config.API_PREFIX + '/{path:path}', methods=METHODS) # /{path:path} fetches everything after the common path prefix
async def redirect(path: str, request: Request):
    """Forward any /api/v1/<service>/... request from the sender to the receiver service."""
    started = time.perf_counter()
    response = await handle_request(path, request)
    duration_ms = (time.perf_counter() - started) * 1000
    logger.info('%s %s -> %s (%.0f ms)', request.method, request.url.path, response.status_code, duration_ms)
    return response


async def handle_request(path, request):
    # if URL is ex: /api/v1/inventory/stock  ->  path = "inventory/stock"  ->  service = "inventory"
    service = path.split('/', 1)[0]
    base_url = config.SERVICES.get(service)  # "http://127.0.0.1:8002" (if inventory)
    if base_url is None:
        return json_error(404, 'Unknown route.')

    # Headers sent to the service
    # Only adds what we choose. Anything else the client sent is never added
    # this prevents malware or someone from inserting damaging or incompatible data in the headers
    headers = {}
    for name in COPIED_REQUEST_HEADERS:  # 'content-type', 'accept'
        if name in request.headers:
            headers[name] = request.headers[name]

    # The request's token is passed on to the service
    # each service will then receive it, send it back to the Gateway when sending a request,
    # and it will then be re-evaluated by the Gateway each time
    token_header = request.headers.get('authorization')  # Bearer token
    if token_header:
        headers['authorization'] = token_header

    # checks who the user is
    # Skipped for the public routes (login)
    method = request.method
    clean_path = request.url.path

    if clean_path.endswith('/'):
        clean_path = clean_path[:-1]  # removes a trailing "/" if there is one

    is_public = False
    if (method, clean_path) in config.PUBLIC_ROUTES:
        is_public = True

    if not is_public:
        try:
            user_id, role = read_user(token_header)
        except AuthError as error:  # if the token is missing, expired or invalid
            return json_error(401, str(error), {'WWW-Authenticate': 'Bearer'})
        headers['x-user-id'] = user_id
        headers['x-user-role'] = role

    # builds the address of the service route to call
    url = base_url + request.url.path  # ex: http://127.0.0.1:8002 + /api/v1/inventory/stock
    if request.url.query:  # if the request has a filter, ex: "type=ADJUSTMENT&limit=50" from the inventory service
        url = url + '?' + request.url.query

    body = await request.body() # asynchronous

    # request.app.state.client: the shared HTTP client made at startup (lifespan); reusing it is faster
    # service: the receiver service, only used by forward() to write the error message if needed ("The inventory service is unavailable.")
    # request.method: the service must receive the same action the client asked for (GET, POST, PUT...)
    # url: where to send it (receiver service address + same path + same query string)
    # headers: only the headers the gateway chose, including x-user-id and x-user-role from the token
    # body: the client's JSON, unchanged, so the service receives the same data
    return await forward(request.app.state.client, service, request.method, url, headers, body) # asynchronous
