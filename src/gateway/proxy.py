"""
Gateway Proxy Module

This module sends the sender's request to the receiver service (the service the request is meant for)
and gives the receiver's answer back unchanged (same status code, same JSON body).
If the receiver cannot be reached, the gateway makes its own answer: 503.

    Sender (POS or a service)  ->  Gateway  ->  Receiver service
                               <-           <-  answer

Author: Zacchary Bedard-Chenier
Date: 26/11/2026
Version: 1.0
"""

import httpx
from fastapi.responses import Response

from .errors import json_error

# Headers of the receiver service's answer that are not copied:
# the gateway sets them again itself before returning the response to the original sender
# these are some default headers from uvicorn and FastAPI
SKIPPED_RESPONSE_HEADERS = {
    'content-length', 'content-encoding', 'transfer-encoding',
    'connection', 'keep-alive', 'date', 'server',
}


async def forward(client, service, method, url, headers, body):
    """Sends the sender's request to the receiver service and returns the receiver's answer.

    Args:
        client (httpx.AsyncClient): The HTTP client shared by the gateway.
        service (str): Name of the receiver service (ex: 'inventory'), used in the error messages.
        method (str): HTTP method (GET, POST, ...).
        url (str): Full address of the route on the receiver service, with the query string.
        headers (dict): Headers to send (chosen by the gateway, never copied blindly).
        body (bytes): The JSON body of the request, or empty.

    Returns:
        Response: The answer of the receiver service, unchanged,
        or a 503 {"detail": ...} made by the gateway if the receiver cannot be reached.
    """
    try:
        answer = await client.request(method, url, headers=headers, content=body)
    except httpx.HTTPError:  # if the Gateway cannot reach the receiver
        return json_error(503, f'The {service} service is unavailable.')

    response_headers = {}
    for name, value in answer.headers.items(): # each header of the receiver's answer
        if name.lower() not in SKIPPED_RESPONSE_HEADERS: # keeps it unless it is on the skip list
            response_headers[name] = value
    return Response(content=answer.content, status_code=answer.status_code, headers=response_headers)
