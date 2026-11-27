# Inventory Service: Inputs and Outputs

All routes start with `/api/v1/inventory`. All bodies and responses are JSON.

## Common to every route

**Headers (sent by the API Gateway):**
- `X-User-Id` (int): id of the user making the request.
- `X-User-Role` (`employee` or `manager`, always in lowercase): role of the user.

**Formats:**
- Quantities are strings with 3 decimals (`"750.000"`), in the unit of the ingredient (`ml`, `g` or `unit`).
- Money is a string with 2 decimals (`"28.50"`).
- Dates are `YYYY-MM-DD`, date-times are (`2026-11-22T14:03:00`).

**Errors:**
- `401`: a user header is missing or the role is unknown.
- `403`: the route is Manager only.
- `404`: unknown ingredient, lot or supplier order.
- `409`: operation not allowed (name already used, stock would become negative, returning more than was taken).
- `422`: invalid data (wrong type, missing field, value out of range).
- Error body: `{"detail": "message"}`, the same format as FastAPI and the API Gateway.
  For a `422` sent by FastAPI itself, `detail` is a list of the invalid fields, not a string.
- A `500` only says what the service was doing; the cause is written in the service's log.

---

## Ingredients

### `GET /ingredients` (any user)
Lists every ingredient, sorted by name.
- **Output `200`:** `{"ingredients": [{"id", "name", "mesure_unit", "reorder_threshold", "shelf_life_days"}]}`
  - `shelf_life_days` is `null` when the ingredient never expires.

### `POST /ingredients` (Manager)
Creates an ingredient.
- **Input:** `{"name", "mesure_unit", "reorder_threshold"?, "shelf_life_days"?}`
  - `name`: unique, 1 to 100 characters, not blank.
  - `mesure_unit`: `ml`, `g` or `unit`.
  - `reorder_threshold`: whole number ≥ 0, default `0` (no alert).
  - `shelf_life_days`: whole number ≥ 1, absent = never expires.
- **Output `201`:** the created ingredient (same fields as the list).
- **Errors:** `409` name already used.

### `PATCH /ingredients/{ingredient_id}` (Manager)
Updates an ingredient. Only the fields sent are changed.
- **Input:** any of `name`, `mesure_unit`, `reorder_threshold`, `shelf_life_days`.
  - `shelf_life_days: null` means the ingredient now never expires. `null` is refused for the other fields.
- **Output `200`:** the updated ingredient.
- **Errors:** `400` no field sent, `404` unknown ingredient, `409` name already used or `null` field.

---

## Stock and alerts

### `GET /stock` (any user)
Usable stock of every ingredient (lots with quantity > 0 that are not expired), sorted by name.
- **Output `200`:** `{"stock": [{"ingredient_id", "name", "mesure_unit", "usable_quantity", "reorder_threshold", "below_threshold", "next_expiry"}]}`
  - `below_threshold`: `true` if the usable stock is under the reorder threshold.
  - `next_expiry`: soonest expiry date among the usable lots, `null` if none expires.

### `GET /stock/{ingredient_id}` (any user)
Usable stock of one ingredient.
- **Output `200`:** one stock level (same fields as above).
- **Errors:** `404` unknown ingredient.

### `GET /alerts` (Manager)
Every ingredient whose usable stock is under its reorder threshold.
- **Output `200`:** `{"alerts": [{"ingredient_id", "name", "usable_quantity", "reorder_threshold"}]}`

---

## Client orders (called by the order service)

### `POST /deductions` (any user)
`+` pressed on the POS: deducts all the ingredients of one item, or nothing. The lots that expire first are used first.
- **Input:** `{"order_id", "button_press_id", "items": [{"ingredient_id", "quantity"}]}`
  - `button_press_id`: unique id of the press (1 to 64 characters). Sending the same id again does not deduct twice.
  - `items`: at least one, each ingredient only once, `quantity` > 0.
- **Output `200`:** `{"order_id", "success", "shortages": [{"ingredient_id", "requested", "available"}], "alerts": [...]}`
  - `success: false` with `shortages` when the stock is not enough: nothing was deducted, the item must not be added.
  - `alerts`: ingredients that just went under their reorder threshold because of this deduction (same format as `/alerts`).
- **Errors:** `404` unknown ingredient.

### `POST /returns` (any user)
`-` pressed on the POS: gives back the ingredients of an item removed from the order, to the same lots they were taken from.
- **Input:** same as `/deductions` (`order_id`, `button_press_id`, `items`). Sending the same id again does not give back twice.
- **Output `200`:** `{"message"}`
- **Errors:** `404` unknown ingredient, `409` the order never took that much of an ingredient.

---

## Adjustments

### `POST /adjustments` (Manager)
Manual change of one lot: a loss (breakage, spoilage, spill) or a correction after a physical count.
- **Input:** `{"lot_stock_id", "quantity_change", "reason"}`
  - `quantity_change`: negative = loss, positive = correction, cannot be `0`.
  - `reason`: 1 to 255 characters, not blank.
- **Output `201`:** `{"movement": {...}, "alert": {...} | null}`
  - `movement`: same format as `/movements`.
  - `alert`: set if this change brought the ingredient under its reorder threshold.
- **Errors:** `404` unknown lot, `409` the lot would become negative.

---

## Supplier orders (restocking)

### `POST /supplier-orders` (Manager)
Places a supplier order. It is received immediately: each line becomes its own lot, and the stock goes up right away. The expiry date of each lot is the order day + the shelf life of its ingredient.
- **Input:** `{"lines": [{"ingredient_id", "quantity", "unit_price"}]}`
  - At least one line, no maximum. `quantity` > 0, `unit_price` ≥ 0.
- **Output `201`:** `{"id", "placed_by", "order_date", "status", "total", "lines": [{"id", "ingredient_id", "lot_stock_id", "quantity", "unit_price"}]}`
  - `status` is always `RECEIVED`. `lines` are sorted by ingredient name.
- **Errors:** `404` unknown ingredient (nothing is saved).

### `GET /supplier-orders` (Manager)
Every supplier order with its lines, newest first.
- **Output `200`:** `{"supplier_orders": [...]}` (same format as above).

### `GET /supplier-orders/{order_id}` (Manager)
One supplier order with its lines.
- **Output `200`:** one supplier order.
- **Errors:** `404` unknown supplier order.

---

## Movement history

### `GET /movements` (Manager)
Every change made to the stock, newest first.
- **Input (query string, all optional):**
  - `type`: `RESTOCK`, `DEDUCTION`, `RETURN` or `ADJUSTMENT`.
  - `ingredient_id`, `lot_stock_id`, `order_id`.
  - `date_from`, `date_to`: `YYYY-MM-DD`, both days included.
  - `limit`: 1 to 500, default 100.
- **Output `200`:** `{"movements": [{"id", "lot_stock_id", "type", "quantity_change", "order_id", "reason", "user_id", "created_at"}]}`
  - `quantity_change`: negative = the stock went down, positive = it went up.

## Settings

Values that depend on team decisions (route prefix, header names, role values, name of the database
variable, port) are in `config.py`. Change them there only.
