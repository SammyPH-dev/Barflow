"""
Inventory Models Package

This package groups the database models of the inventory service (one class per file).

Author: Zacchary Bedard-Chenier
Date: 20/11/2026
Version: 1.0
"""

# every model needs to be imported here before Base.metadata.create_all() in database_connection.py
# so Python knows them and can add their tables to SQLAlchemy
from .base import Base
from .enums import MesureUnit, MovementType, SupplierOrderStatus
from .ingredient import Ingredient
from .lot_stock import LotStock
from .stock_movement import StockMovement
from .supplier_order import LigneSupplierOrder, SupplierOrder
