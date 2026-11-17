# syntax=docker/dockerfile:1.7
# Multi-stage Dockerfile optimisé pour FastAPI avec UV (Astral)
# Permet des builds ultra-rapides, une image finale minimale et sécurisée

# ==============================================================================
# Étape 1 : Image binaire UV officielle
# ==============================================================================
FROM ghcr.io/astral-sh/uv:0.6.3 AS uv_bin

# ==============================================================================
# Étape 2 : Builder - Compilation & Installation des Dépendances
# ==============================================================================
FROM python:3.12-slim-bookworm AS builder

# Copier le binaire uv depuis l'étape dédiée
COPY --from=uv_bin /uv /bin/uv

WORKDIR /build

# Optimisations du compilateur UV
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

# Installer les dépendances système requises pour compiler d'éventuels packages C
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de dépendances
COPY pyproject.toml .

# Installer l'environnement virtuel avec UV
RUN --mount=type=cache,target=/root/.cache/uv \
    uv venv /app/.venv && \
    uv pip install --python /app/.venv/bin/python -r pyproject.toml

# ==============================================================================
# Étape 3 : Cible Développement (avec rechargement à chaud et outils de dev)
# ==============================================================================
FROM python:3.12-slim-bookworm AS development

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/.venv /app/.venv
COPY . /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=development

EXPOSE 8000

RUN chmod +x /app/entrypoint.sh 2>/dev/null || true

ENTRYPOINT ["/app/.venv/bin/python", "/app/scripts/entrypoint.py"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ==============================================================================
# Étape 4 : Cible Production Finale (Légère, Sécurisée & Non-Root)
# ==============================================================================
FROM python:3.12-slim-bookworm AS production

# Client PostgreSQL pour les tests de santé
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Créer un utilisateur et un groupe système dédiés non-root
RUN groupadd -r kolix && useradd -r -g kolix -d /app -s /sbin/nologin kolix

WORKDIR /app

# Copier uniquement l'environnement virtuel et le code applicatif
COPY --from=builder --chown=kolix:kolix /app/.venv /app/.venv
COPY --chown=kolix:kolix . /app

# Variables d'environnement pour l'exécution
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    PORT=8000

USER kolix

EXPOSE 8000

ENTRYPOINT ["/app/.venv/bin/python", "/app/scripts/entrypoint.py"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--lifespan", "on"]

