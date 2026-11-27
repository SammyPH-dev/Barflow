
from urllib import request

from fastapi import APIRouter, Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from common.database import get_db
from services.orders.model import OrderItem
from services.orders.schema import OrderCreate, OrderItemCreate, OrderItemResponse, OrderResponse, OrderStatusUpdate, OrderitemUpdate
from services.orders.service import OrderService



#creating app
router = APIRouter(prefix="/api/v1/orders", tags=["orders"])
order_service=OrderService()

#----------------------------#
#  ORDERS                    #
#----------------------------#

# CREATE
@router.post(
    "/",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_order(data:OrderCreate, db:Session = Depends(get_db)):
    order = order_service.create_order(db, data)
    if order is None:
        raise HTTPException(status_code=400, detail="Order data is required")
    return order

# READ
@router.get("/{order_id}", response_model=OrderResponse)
async def read_order(order_id: int, db:Session = Depends(get_db)):
    order = order_service.fetch_order(db, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

# READ ALL
@router.get("/", response_model=list[OrderResponse])
async def read_all_order(db:Session = Depends(get_db)):
    return order_service.fetch_all_orders(db)

# UPDATE ORDER
@router.put("/{order_id}", response_model=OrderResponse)
async def update_orders(order_id: int, data:OrderStatusUpdate, db:Session = Depends(get_db)):
    order = order_service.update_order_status(db, order_id, data)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

# DELETE ORDER
@router.delete("/{order_id}", response_model=bool)
async def delete_order(order_id: int, db:Session = Depends(get_db)):
    deleted = order_service.delete_order(db, order_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Order not found")
    return deleted


#----------------------------#
#  ORDER ITEMS               #
#----------------------------#

# ADD ORDER ITEM
@router.post(
    "/{order_id}/order_items/",
    response_model=OrderItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_order_item(order_id: int, data:OrderItemCreate, db:Session = Depends(get_db)):
    created_items = order_service.add_order_item(db, order_id, [data])
    if not created_items:
        raise HTTPException(status_code=404, detail="Order or recipe not found")
    return created_items[0]

# REMOVE ORDER ITEM
@router.delete("/order_items/{order_item_id}", response_model=bool)
async def remove_order_item(order_item_id: int, db:Session = Depends(get_db)):
    order_item=db.get(OrderItem, order_item_id)
    if order_item is None:
        raise HTTPException(status_code=404, detail="Order item not found")
    return order_service.remove_order_item(db, order_item)

# UPDATE ORDER ITEM
@router.put("/order_items/{order_item_id}", response_model=OrderItemResponse)
async def update_order_item(order_item_id: int, data:OrderitemUpdate, db:Session = Depends(get_db)):
    return order_service.update_order_item(db, order_item_id, data)

