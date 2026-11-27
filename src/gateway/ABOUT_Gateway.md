# API Gateway

The gateway is the only entry point of the back end. The **sender** (the front end POS, or a service)
sends every request to it, and it forwards the request to the **receiver service**, the one the request
is meant for. Everything that goes through it is JSON.

```
Sender (POS or a service)  ->  Gateway  ->  Receiver service
                           <-          <-   answer
```

In this document, "sender" and "receiver service" always have these meanings. The answer of the receiver
service goes back to the sender through the gateway, unchanged.

Author: Zacchary Bedard-Chenier
Date: 26/11/2026

---

## To discuss with the team

Everything the team has to decide or adjust is here. The gateway service had to assume how the other parts behave.

### 1. Rules for every service

| `<service>` | Owner | Port |
|---|---|---|
| `gateway` | Zacchary | 8000 |
| `login` | Bruno | 8001 |
| `inventory` | Zacchary | 8002 |
| `orders` | (not started) | 8003 |
| `recipes` | (not started) | 8004 |
| `recommendations` | Sammy | 8005 |
| `discounts` | (not started) | 8006 |

- Every route starts with `/api/v1/<service>`. The gateway forwards the path unchanged, so a service with another
  prefix is not found. Each service is its own application, on its own port.
- A service **never checks the token**. It trusts `X-User-Id` (whole number) and `X-User-Role` (`manager` or
  `employee`, lowercase), which only the gateway sets.
- Errors use `{"detail": "message"}`. Bodies are JSON (`Content-Type: application/json`).
- A service that needs another service calls **the gateway** (`http://127.0.0.1:8000/api/v1/...`), never the
  other service directly, and sends the **same `Authorization` header** it received. The user's identity follows
  the call.
- Only `Content-Type`, `Accept`, `Authorization`, `X-User-Id` and `X-User-Role` reach a service. If one needs another
  header, add it to `COPIED_REQUEST_HEADERS` in `main.py`.
- A service answers within 5 seconds (POS actions are expected under 300 ms, reports under 2 s). Otherwise the gateway
  answers 503 (there is no separate timeout handling).

### 2. Login service (Bruno)

- **Port and routes.** Port **8001** (*today: hard-coded to 8000 in `main.py`, the gateway's port*). Routes
  `POST /api/v1/login`, `GET /api/v1/login/recent-users`, `GET /api/v1/login/me` (*today: the prefix is `/login`*).
  `/me` still reads the token itself: the gateway passes `Authorization` on.
- **The login service only has to return a signed token.** It looks the user up by email, checks the credentials,
  and signs a token with HS256. The gateway never looks users up. The token must contain:

  | Claim | Content | Used for |
  |---|---|---|
  | `sub` | the stable identifier of the user, as a string of digits (ex: `"7"`) | becomes `X-User-Id` |
  | `role` | `manager` or `employee` (any case, the gateway lowercases it) | becomes `X-User-Role` |
  | `exp` | expiry (*today: 30 minutes, OK*) | the gateway refuses an expired token |

  *Today: `sub` is the **email**, which the gateway refuses (it accepts digits only). Login must change, not the
  gateway.* The response of `POST /api/v1/login` may also contain a `user` object (name, role) **for the display only**
  (ex: to show the Manager-only tabs). The gateway ignores it and the services never trust it.
- **Why an identifier is still needed**, even though the email is unique: the services record **who did what**. The
  inventory service stores it on every stock movement (deductions, returns, Manager adjustments, supplier orders) and
  returns it in the movement history. The role alone is not enough. The email is a poor identifier: it is personal data
  (Loi 25) copied into every record, and if a user changes email the old history no longer matches.
- **To decide:** which identifier goes in `sub`: the user id or the employee number (`empNumb`)? The gateway
  accepts **digits only**. If it is not numeric, `auth.py` and the `X-User-Id` handling of the services
  (inventory: `int`) must change together.
- **To decide (Loi 25):** `GET /api/v1/login/recent-users` is public and sends names and emails without a token, because
  the login screen shows them before anyone is logged in. Is that acceptable? Only this route and
  `POST /api/v1/login` are public.
- **The secret.** `JWT_SECRET_KEY` is in the login service's `local_settings.py`. The gateway has its own
  `local_settings.py` and **must contain the same value** (at least 32 characters), shared by hand between the
  team's machines, never through Git. If the values differ, every token is refused (401).

### 3. Other services

- **Recommendation (Sammy).** Port **8005**, routes `/api/v1/recommendations/...` (ex: `GET .../drinks`).
  *Today: no `main.py` (the old gateway imported its router directly, the new one does not), and the prefix is
  `/recommendations`.* So it must run as its own application like the login service. To read the stock (and later the
  sales), it calls the gateway, ex: `GET /api/v1/inventory/stock`, with the `Authorization` it received.
- **Orders (not started).** Port **8003**, routes under `/api/v1/orders`. On **+** and **-** on the POS, it calls
  `POST /api/v1/inventory/deductions` and `POST /api/v1/inventory/returns` through the gateway. The bodies are in
  `src/services/inventory/ABOUT_inventory_service.md`.
- **Recipes (not started).** Port **8004**, routes under `/api/v1/recipes`. The inventory page of the POS will read
  the recipes from it (mock data for now).
- **Discounts (not started).** Port **8006**, routes under `/api/v1/discounts`.

### 4. Front end (POS)

- **Same origin, no CORS.** The gateway has no CORS setting. The POS and the gateway must be on the **same origin**
  (same protocol, domain **and port**), otherwise the browser blocks the answers and CORS (`CORSMiddleware`) must
  be added to the gateway. CORS only exists in browsers: services, curl and Postman are not affected.
  - *Development:* the POS runs on `http://localhost:5173` (Vite) and the gateway on `http://localhost:8000`.
    Different port, so **not** the same origin. Use the Vite proxy so the browser only talks to port 5173
    (in `vite.config.ts`): `server: { proxy: { '/api': 'http://localhost:8000' } }`, and call the relative address
    `/api/v1/...` (`VITE_API_GATEWAY_URL` left empty).
  - *Production on AlwaysData:* serve the POS and the gateway under the same domain, ex:
    `https://barflow.alwaysdata.net/` for the site and `https://barflow.alwaysdata.net/api/...` for the gateway.
- Every request sends `Authorization: Bearer <token>`, except the two public login routes. Never send
  `X-User-Id` / `X-User-Role`: the gateway ignores them.
- Errors: read `detail`. For a `422` made by FastAPI, `detail` is a **list** of invalid fields, not a string.
- The POS is only ever a **sender**: it has no server, so a service cannot push something to it. Today the POS asks
  (ex: `GET /api/v1/inventory/alerts`). If pushing is needed later: polling, or WebSocket / Server-Sent Events
  (the gateway would have to support them).

### 5. Secrets, Docker and deployment

- **Limitation today.** The gateway reads `JWT_SECRET_KEY` **only** from `local_settings.py` (not in Git) and the
  service addresses are written in `SERVICES` in `config.py`. In Docker this fails: built from a Git clone, the file is
  missing and the gateway refuses to start; built from the working folder, the secret ends up **inside the image**; and
  a secret given as an environment variable is ignored. The login service has the same limitation.
- **Goal: the teacher runs `docker compose up` and everything works right away**, with no file to create and no variable to
  set. Two things in the code block it: the secret (above) and the addresses: `127.0.0.1` inside a container means
  "this container itself", so the gateway would never reach a service (every request: 503). In Compose, a service is
  reached by its **name** (ex: `http://inventory:8002`).
- **What needs to change**
  - *Gateway:* read each service address from an environment variable **with the current value as default**
    (`os.environ.get('INVENTORY_SERVICE_URL', 'http://127.0.0.1:8002')`); read the secret from the environment
    first, then `local_settings.py` (`os.environ.get('JWT_SECRET_KEY') or JWT_SECRET_KEY`); a `Dockerfile` that starts
    `uvicorn src.gateway.main:app --host 0.0.0.0 --port 8000` (`0.0.0.0` so the container accepts outside connections).
    Local development stays as it is today.
  - *Login:* read the secret from the environment too, port 8001, prefix `/api/v1/login`, a `Dockerfile`.
  - *Inventory:* already reads `DATABASE_URL`. Needs a `Dockerfile` and `--host 0.0.0.0 --port 8002`.
  - *Every other service:* a `Dockerfile`, its own port, `--host 0.0.0.0`, routes under `/api/v1/<service>`, its
    database URL from an environment variable. Services call each other through `http://gateway:8000/api/v1/...`.
  - *Database:* a private AlwaysData database is fragile for a demo. The simplest is a MariaDB container in the
    compose file, with the services' `DATABASE_URL` pointing to it by name. Inventory creates its tables and its
    default ingredients on an empty database.
  - *POS:* one web server container (ex: nginx) serving the built POS and sending `/api/...` to the gateway, so there is
    no CORS.
  - *`docker-compose.yml`* (new, at the root): one entry per container, the variables below, `depends_on` so the database
    starts first. Only the web server needs a published port (ex: `80:80`): the gateway and the services stay unreachable
    from outside Docker.

  ```yaml
  gateway:
    environment:
      JWT_SECRET_KEY: "demo-secret-at-least-32-characters-long"   # demo only, same value as login
      LOGIN_SERVICE_URL: "http://login:8001"
      INVENTORY_SERVICE_URL: "http://inventory:8002"
      ORDERS_SERVICE_URL: "http://orders:8003"
      RECIPES_SERVICE_URL: "http://recipes:8004"
      RECOMMENDATIONS_SERVICE_URL: "http://recommendations:8005"
      DISCOUNTS_SERVICE_URL: "http://discounts:8006"
  inventory:
    environment:
      DATABASE_URL: "mysql+pymysql://user:password@database/inventory"
  ```

  A secret written in a committed file is acceptable for a school demo only, clearly labelled demo-only and never
  used anywhere real (AlwaysData must use a different secret).
- **AlwaysData.** The services trust `X-User-Role` blindly, so **only the gateway may be reachable from the Internet**.
  If AlwaysData makes each service public, add a shared secret header (ex: `X-Gateway-Key`) that the gateway sends and
  every service checks. Check how AlwaysData gives the address and port of a Python (ASGI) site.
- **To decide:** who writes the `Dockerfile` of each service and the compose file, and whether the database is a
  container or the AlwaysData one.

### 6. Choices made inside the gateway (can be changed)

- A token whose role is not `manager` or `employee`, or whose `sub` is not a number, is refused (401).
- The gateway refuses to start without a valid `JWT_SECRET_KEY`, instead of failing on the first request.
- `GET /` still answers `{"message": "API is online"}` (kept from the first version of the gateway).
- `127.0.0.1` is used instead of `localhost` for the services: on Windows, `localhost` can add a delay to every call.

---

## What happens on each request

1. **Find the service.** Unknown `<service>`: `404 {"detail": "Unknown route."}`.
2. **Check the token** (not for the public routes): signature (HS256 with `JWT_SECRET_KEY`), expiry,
   a numeric user id in `sub` and a known role in `role`. Otherwise `401 {"detail": "..."}`.
3. **Say who the user is.** Any `X-User-Id` / `X-User-Role` sent by the client is dropped, and the
   gateway adds its own from the token:
   - `X-User-Id`: the user id (digits, ex: `7`)
   - `X-User-Role`: `manager` or `employee`, **always in lowercase**
4. **Forward** the method, path, query string and JSON body. Only these headers reach the service:
   `Content-Type`, `Accept`, `Authorization`, `X-User-Id`, `X-User-Role`. Every other header is dropped.
5. **Send the receiver service's answer back to the sender unchanged** (same status code, same JSON body).
   If the receiver service cannot be reached, the gateway makes its own answer:
   - `503 {"detail": "The <service> service is unavailable."}`: the receiver service could not be reached
     (not running, too slow, or broken answer). There is no separate timeout handling: the HTTP client
     uses the default `httpx` wait of 5 seconds.

Every error uses the FastAPI format: `{"detail": "message"}`.

The gateway logs one line per request (method, path, status, duration). It never logs the token,
the body or the query string (Loi 25).

## How the gateway works (full flow)

```
Sender (POS or a service)  ->  Gateway (port 8000)  ->  Receiver service (8001-8006)
                           <-                       <-   answer
```

**The POS is only ever a sender, never a receiver.** It is a web page in the browser: it has no server and no
address the gateway could call, and it is not in the list of services (`config.SERVICES`). A request for
anything that is not a listed service gets a 404. What the POS receives is the **answer** to a request it
sent, which is not the same as receiving a request:

```
POS asks:            POS  ->  Gateway  ->  Inventory service   (POS = sender, Inventory = receiver)
Inventory answers:   POS  <-  Gateway  <-  Inventory service   (the answer travels back to the sender)
```

A service therefore cannot push something to the POS on its own (ex: "stock is low, show an alert now").
Today the POS asks (ex: `GET /api/v1/inventory/alerts`). If pushing is needed later, the options are
polling (the POS asks regularly) or a connection that the POS opens and keeps (WebSocket or Server-Sent
Events), which the gateway would have to support.

The gateway does three jobs and nothing else:
1. **Find** which service the request is for.
2. **Check who the user is**, from the token.
3. **Pass the request on** to the receiver service and **pass its answer back**, unchanged.

### Start-up (`lifespan` in `main.py`)

- `config.get_jwt_secret()` checks that `JWT_SECRET_KEY` exists (at least 32 characters). If not, the gateway
  **refuses to start**, instead of failing on the first request.
- One shared HTTP client is created (`app.state.client`) and reused by every request.
- When the gateway stops, the `finally` closes the client.

### A request arrives

Example: an employee's POS calls `GET /api/v1/inventory/movements?limit=50` with `Authorization: Bearer <token>`.

FastAPI matches the catch-all route `/api/v1/{path:path}` and calls `redirect(path, request)`:
- `path` = `"inventory/movements"` (what comes after `/api/v1/`);
- `request` = the object with the method, URL, headers and body.

`redirect` starts a timer, calls `handle_request`, writes **one log line** (method, path, status, duration;
never the token, the body or the query string) and returns the response.

### Inside `handle_request`

| # | What it does | Example |
|---|---|---|
| 1 | **Find the receiver service.** The first word of `path` is looked up in `config.SERVICES`. Unknown: **404**. | `"inventory"` -> `http://127.0.0.1:8002` |
| 2 | **Build the headers to send.** Start with an empty dict. Copy only `content-type` and `accept` from the sender, plus `authorization`. Every other header is never copied, including a fake `X-User-Role`. | `{accept, authorization}` |
| 3 | **Check the user.** Unless the route is public, `read_user` checks the token: signature, expiry, numeric `sub`, known `role`. Any problem: **401**, nothing is forwarded. If valid, the gateway adds `x-user-id` and `x-user-role` itself. | `x-user-id: 8`, `x-user-role: employee` |
| 4 | **Build the address** on the receiver service: its address + the same path + the same query string. | `http://127.0.0.1:8002/api/v1/inventory/movements?limit=50` |
| 5 | **Send and return.** Read the body, call `forward()` (in `proxy.py`) and return what comes back. | |

### `forward()`

It sends the request to the receiver service with the shared client.
- **The receiver answers** (even with 403, 404, 409, 422...): the gateway returns that answer **unchanged**
  (same status, same JSON). Only a few headers that the gateway's own server sets are skipped.
- **The receiver cannot be reached** (not running, too slow, broken answer): the gateway makes its own
  answer, **503** `{"detail": "The <service> service is unavailable."}`.

In the example, inventory answers `403` because the movements are Manager-only, and the POS receives exactly that.

### Why it is built this way

- **Services never check tokens.** Only the gateway does. The services trust `X-User-Id` and `X-User-Role`.
  This is safe only because the gateway is the only way in and overwrites those headers (steps 2 and 3).
- **The gateway does not understand the business.** It never reads the JSON, so a new route in a service works
  without any gateway change, and a value like `"4.50"` is never altered on the way.
- **One door.** The POS only knows the gateway's address. Services also talk to each other through the gateway,
  passing the same `Authorization` header.

### Who answers in each case

| Situation | Who answers | Status |
|---|---|---|
| Unknown `<service>` | gateway | 404 |
| Missing, expired or invalid token | gateway | 401 |
| Receiver service unreachable | gateway | 503 |
| Anything else (business rules, permissions, validation) | receiver service, passed back unchanged | whatever it sends |
