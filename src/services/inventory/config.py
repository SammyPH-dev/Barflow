"""
Inventory Service Configuration Module

Values that depend on team decisions or on how the parts of the system talk to each other.
When the team changes one of them (route prefix, header names, roles), change it here only.

Author: Zacchary Bedard-Chenier
Date: 27/11/2026
Version: 1.0
"""

# Public prefix of the routes (team convention: /api/v1/<service>)
API_PREFIX = '/api/v1/inventory'

# Headers added by the API Gateway, and the role values it sends (always lowercase)
USER_ID_HEADER = 'X-User-Id'
USER_ROLE_HEADER = 'X-User-Role'
EMPLOYEE_ROLE = 'employee'
MANAGER_ROLE = 'manager'
ROLES = (EMPLOYEE_ROLE, MANAGER_ROLE)

# Name of the environment variable that holds the database URL
# (only the name is here: the URL contains the password, so it is never written in the code)
DATABASE_URL_VARIABLE = 'DATABASE_URL'

# Port expected by the gateway (INVENTORY_SERVICE_URL), used in the run command:
#     uvicorn services.inventory.main:app --port 8002
PORT = 8002
