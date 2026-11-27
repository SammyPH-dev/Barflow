from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from services.orders.model import OrderStatus

# defines how data enters and leaves your HTTP endpoints via JSON.

#change to push
# === Orderitem Schemas ===

class OrderItemBase(BaseModel):
    recipes_id: int = Field(..., gt=0, description="ID of the cocktail/drink recipe")
    quantity: int = Field(default=1, ge=1, le=50, description="Number of units ordered")
    special_instructions: Optional[str] = Field(default=None, max_length=255, examples=["No ice", "Extra lime"])

class OrderItemCreate(OrderItemBase):
    pass

class OrderitemUpdate(BaseModel):
    quantity: Optional[int] = Field(default=None, ge=1, le=50)
    special_instructions: Optional[str] = Field(default=None, max_length=255)

class OrderItemResponse(OrderItemBase):
    id:int
    order_id: int
    unit_price: Decimal
    line_total: Decimal
    model_config = ConfigDict(from_attributes=True)

# Order Schemas

class OrderCreate(BaseModel):
    table_number: Optional[str] = Field(default=None, max_length=20, examples=["T-04", "BAR-2"])
    promo_code: Optional[str] = Field(default=None, max_length=50, description="Optional promo code to evaluate")
    notes: Optional[str] = Field(default=None, max_length=255)
    items: List[OrderItemCreate] = Field(default_factory=list, description="Initial drinks added to the order")

class OrderStatusUpdate(BaseModel):
    status: OrderStatus
    tip_amount: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"))

class ApplyDiscountRequest(BaseModel):
    promo_code: str = Field(..., min_length=1, max_length=50)

class OrderResponse(BaseModel):
    id:int
    table_number: Optional[str]
    bartender_id:Optional[int]
    discount_id: Optional[int]
    status: OrderStatus

    subtotal:Decimal
    discount_amount:Decimal
    tax_gst:Decimal
    tax_qst:Decimal
    tip_amount:Decimal
    total_amount:Decimal

    notes:Optional[str]
    created_at:datetime
    updated_at:datetime
    items:List[OrderItemResponse] = Field(default_factory=list)
    model_config=ConfigDict(from_attributes=True)

