"""
Inventory Enumerations Module

This module defines the fixed lists of values used by the inventory models:
measure units, supplier order statuses and stock movement types.

Author: Zacchary Bedard-Chenier
Date: 20/11/2026
Version: 1.0
"""

import enum


# unit an ingredient is measured in
class MesureUnit(str, enum.Enum):
    ML = 'ml'
    G = 'g'
    UNIT = 'unit'


# life cycle of a supplier order (an order to refill the inventory, NOT a client order):
# DRAFT -> SENT -> RECEIVED
# for now, pressing "Order" on the POS receives the order immediately,
# all its lots are added to the inventory at once.
class SupplierOrderStatus(str, enum.Enum):
    DRAFT = 'DRAFT'
    SENT = 'SENT'
    RECEIVED = 'RECEIVED'


# why the quantity of a lot changed
# every change is saved as a StockMovement
# This is needed to keep the relevant info of an item when it is removed from a client order
# A removed item will go back to the inventory into its assigned lot and keep its original exp_date
class MovementType(str, enum.Enum):
    RESTOCK = 'RESTOCK' # supplier order received, its lots are added to the inventory
    DEDUCTION = 'DEDUCTION' # item added to a client order, + on the POS
    RETURN = 'RETURN' # item removed from a client order, - on the POS
    ADJUSTMENT = 'ADJUSTMENT' # manual change of a lot by the manager: breakage, spoilage, spill or count correction (+ or -)

