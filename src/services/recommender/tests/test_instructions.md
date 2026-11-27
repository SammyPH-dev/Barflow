# Recommender tests

From the Barflow project root, with its virtual environment activated:

```bash
python -m unittest discover -s src/services/recommender/tests -t . -v
```

No running servers, database credentials, or cloud database are needed.
The tests use Python's built-in unittest, plus the project's existing FastAPI,
Pydantic and HTTPX dependencies. No pytest plugin is required.

- test_service.py: expiry boundaries, recipe matching, availability, sorting,
  explanations and orchestration. A fixed date makes results repeatable.
- test_inventory_client.py: request URL/headers, parsed stock, and failures.
  HTTPX MockTransport replaces the network.
- test_schemas.py: conversions, invalid input and response structure.
- test_router.py: endpoint contracts and main application registration.
  TestClient calls the app in process; service calls are mocked.
- test_popularity.py: sales ranking, top-ten limit, availability exclusions,
  sales schema validation, and shared inventory fetching.
- helpers.py: reusable sample stock/recipes and a fixed clock.

The availability and earliest-expiry helpers assume inventory has already removed
expired stock and returns one aggregate entry per ingredient. Sample recipes use
one entry per ingredient. Popularity ranking is tested with sample sales totals; the external order-service
integration is not implemented yet. These tests do not verify the real inventory database,
authentication gateway, or an external recipe service.
