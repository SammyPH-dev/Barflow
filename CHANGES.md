# Code Changes

This list summarizes changes made during this session. It excludes unrelated
changes that were already present in the working tree.

## Docker setup

- Added `Dockerfile` to build a Python 3.14 image for the gateway and inventory
  service.
- Added `compose.yaml` to run the gateway and inventory containers together.
  The gateway is exposed on port 8000 and inventory on port 8002.
- Configured inventory to receive `DATABASE_URL` from the root `.env` file.
  The URL should point to the existing external Alwaysdata database; no
  database container is started.
- Configured the gateway to reach inventory by its Compose service name
  (`inventory:8002`) and to receive `JWT_SECRET_KEY` from the root `.env` file.
- Added `.dockerignore` to exclude environment files, local settings, virtual
  environments, and unrelated frontend/test files from the build context.

## Application configuration

- Updated `src/gateway/config.py` so `INVENTORY_SERVICE_URL` can override the
  local inventory URL. It also reads `JWT_SECRET_KEY` from the environment,
  retaining `gateway/local_settings.py` as a local fallback.
- Added `httpx` to the root `requirements.txt` because the gateway uses it to
  forward requests.
- Corrected `src/services/inventory/config.py` so
  `DATABASE_URL_VARIABLE` is the environment variable name `DATABASE_URL`.

## Validation

- Gateway unit tests: 14 passed.
- `docker compose config --quiet`: passed using dummy validation values.
- Docker image build was not completed because the Docker Desktop Linux engine
  was not running.

## Run locally with Docker Compose

From the repository root, create a private `.env` containing `DATABASE_URL`
and `JWT_SECRET_KEY`, then run:

```powershell
docker compose up --build
```

Do not put real credentials in `.env.example` or commit `.env`.

## Login service and authentication fixes (2026-11-27)

- Added the login service to `compose.yaml`; the gateway now routes to
  `login:8001` and starts after login and inventory.
- Configured the login container to run `services.login.main:app`, and mounted
  its routes under `/api/v1` to match gateway forwarding.
- Updated login imports and JWT secret handling for the container layout and
  shared `JWT_SECRET_KEY` environment variable.
- Added numeric user IDs to login-issued tokens and taught the gateway to use
  that claim while preserving support for legacy numeric `sub` claims.
- Added the `argon2` and Pydantic email-validation extras required by login.

### Latest validation

- Gateway tests: 15 passed.
- `docker compose config -q`: passed.
- Gateway and login images built; gateway, inventory, and login containers
  started.
- Verified login through the gateway and authenticated `/api/v1/login/me`
  using the returned token.
