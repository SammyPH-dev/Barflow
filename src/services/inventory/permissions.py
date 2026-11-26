"""
Inventory Authorization Module

This module checks who is making the request and what role they have.

Every request reaches this service through the API Gateway. The gateway checks the JWT of the user
(signature and expiry), then sends the headers "X-User-Id" and "X-User-Role" (EMPLOYEE or MANAGER).
This service trusts these headers and never checks the token itself.

Author: Zacchary Bedard-Chenier
Date: 20/11/2026
Version: 1.0
"""

from fastapi import Depends, Header, HTTPException

ROLES = ('EMPLOYEE', 'MANAGER')


# Permission check: FastAPI runs these before the route, if one raises an HTTPException the route never runs

def user_required(x_user_id: int | None = Header(default=None),
                  x_user_role: str | None = Header(default=None)):
    """Builds the current user from the headers sent by the API Gateway.

    Returns:
        A dict with the user's id and role.

    Raises:
        HTTPException 401: If a header is missing or the role is unknown.
    """
    if x_user_id is None or x_user_role is None:
        raise HTTPException(status_code=401, detail='The user is missing or not configured properly.')

    if x_user_role not in ROLES:
        raise HTTPException(status_code=401, detail='The role of the user is invalid.')

    return {'id': x_user_id, 'role': x_user_role}


# checks the role on the server, not only in the UI (POS)
def manager_required(user: dict = Depends(user_required)):
    """Only lets a Manager pass.

    Raises:
        HTTPException 403: If the user is not a Manager.
    """
    if user['role'] != 'MANAGER':
        raise HTTPException(status_code=403, detail='You do not have permission to access this resource.')

    return user
