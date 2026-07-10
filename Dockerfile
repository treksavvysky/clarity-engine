# Clarity Engine dev container.
#
#   docker compose up -d --build
#
# Source is bind-mounted by docker-compose.yml and uvicorn runs with
# --reload, so this image only needs to bake in the dependency layer.
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
