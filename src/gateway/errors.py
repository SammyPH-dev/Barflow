"""
Gateway Errors Module

Errors sent by the gateway itself use the same format as FastAPI and every service:
{"detail": "message"}

Author: Zacchary Bedard-Chenier
Date: 26/11/2026
Version: 1.0
"""

from fastapi.responses import JSONResponse


def json_error(status_code, detail, headers=None):
    """Build an error response.

    Args:
        status_code (int): The HTTP status code.
        detail (str): The message for the client.
        headers (dict, optional): Extra headers (ex: WWW-Authenticate for a 401).

    Returns:
        JSONResponse: {"detail": detail} with the given status code.
    """
    return JSONResponse({'detail': detail}, status_code=status_code, headers=headers)
