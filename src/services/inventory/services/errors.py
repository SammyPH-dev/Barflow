"""
Inventory Errors Module

This module defines the errors raised by the inventory business logic.
The routes catch them and send back the matching HTTP status code.

Author: Zacchary Bedard-Chenier
Date: 20/11/2026
Version: 1.0
"""


# base class of every inventory business error ---> HTTP 400
class InventoryError(Exception):
    pass


# unknown ingredient, lot or supplier order ---> HTTP 404
class NotFoundError(InventoryError):
    pass


# operation not allowed in the current state ---> HTTP 409
# ex: if the stock would become negative or if the name is already used...
class InvalidOperationError(InventoryError):
    pass
