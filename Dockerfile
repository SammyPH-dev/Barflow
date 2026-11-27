FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY src ./src
WORKDIR /app/src

EXPOSE 8000 8002

CMD ["uvicorn", "gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]
