import httpx
from .schemas import Stock
"""
Inventory client to run the service as a server

The module calls the inventory service's  /stock endpoint by making it run on its own server. This module run the server
in order to be capable of calling the inventory service without making it a monolithic app.
"""
async def get_inventory_stock(
        base_url: str,
        user_id: int,
        user_role: str
) -> list[Stock]:
    """Request available stock from the inventory service"""

    # Headers necessary for the endpoint. Usually given by the gateway
    headers = {
        "X-User-Id": str(user_id),
        "X-User-Role": user_role
    }

    # Open the http Client and automatically closes after being done with the operation
    async with httpx.AsyncClient(
        base_url=base_url,
        timeout=10,
    ) as client:
        response = await client.get(
            url="/api/v1/inventory/stock",
            headers=headers
        )

        response.raise_for_status()

        data = response.json()

        # Validate each inventory entry and convert it into a Stock object.
        return [Stock.model_validate(item) for item in data["stock"]]


