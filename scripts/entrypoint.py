# scripts/entrypoint.py
import asyncio
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

# Ajouter la racine du projet
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

def wait_for_service(host: str, port: int, service_name: str, max_retries: int = 30, delay: float = 1.5) -> bool:
    print(f"[ENTRYPOINT] En attente du service {service_name} ({host}:{port})...")
    for attempt in range(1, max_retries + 1):
        try:
            with socket.create_connection((host, port), timeout=2.0):
                print(f"[ENTRYPOINT] [OK] {service_name} est prêt et accepte les connexions !")
                return True
        except (OSError, ConnectionRefusedError):
            print(f"[ENTRYPOINT] [{attempt}/{max_retries}] {service_name} n'est pas encore disponible, nouvelle tentative dans {delay}s...")
            time.sleep(delay)
    print(f"[ENTRYPOINT] [ERREUR] Impossible de joindre {service_name} après {max_retries} tentatives.")
    return False

def run_migrations():
    print("[ENTRYPOINT] Exécution automatique des migrations Alembic...")
    res = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=False)
    if res.returncode != 0:
        print("[ENTRYPOINT] [AVERTISSEMENT] Erreur lors des migrations Alembic.")
    else:
        print("[ENTRYPOINT] [OK] Schéma de base de données à jour.")

def run_seed_if_requested():
    auto_seed = os.getenv("AUTO_SEED", "false").lower() in ("true", "1", "yes")
    if auto_seed:
        print("[ENTRYPOINT] Détection de AUTO_SEED=true -> Exécution du script de données initiales...")
        subprocess.run([sys.executable, "scripts/seed.py"], check=False)

def main():
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        from urllib.parse import urlparse
        clean_url = db_url.replace("postgresql+asyncpg://", "http://").replace("postgresql://", "http://").replace("postgres://", "http://")
        try:
            parsed = urlparse(clean_url)
            pg_host = parsed.hostname or "localhost"
            pg_port = parsed.port or 5432
        except Exception:
            pg_host = os.getenv("POSTGRES_SERVER", "localhost")
            pg_port = int(os.getenv("POSTGRES_PORT", "5432"))
    else:
        pg_host = os.getenv("POSTGRES_SERVER", "localhost")
        pg_port = int(os.getenv("POSTGRES_PORT", "5432"))
    
    # 1. Attente de PostgreSQL
    if not wait_for_service(pg_host, pg_port, "PostgreSQL"):
        sys.exit(1)

    # 2. Attente facultative de Redis
    redis_host = os.getenv("REDIS_HOST")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    if redis_host and redis_host != "localhost" and redis_host != "127.0.0.1":
        wait_for_service(redis_host, redis_port, "Redis", max_retries=15, delay=1.0)

    # 3. Migrations Alembic
    skip_migrations = os.getenv("SKIP_MIGRATIONS", "false").lower() in ("true", "1", "yes")
    if not skip_migrations:
        run_migrations()

    # 4. Données initiales
    run_seed_if_requested()

    # 5. Démarrer le processus passé en argument (CMD) en tenant compte de $PORT et $WEB_CONCURRENCY
    port = os.getenv("PORT", "8000")
    workers = os.getenv("WEB_CONCURRENCY", "1")
    cmd = sys.argv[1:]
    if not cmd:
        cmd = ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", str(port), "--workers", str(workers), "--lifespan", "on"]
    else:
        if "--port" in cmd:
            idx = cmd.index("--port")
            if idx + 1 < len(cmd):
                cmd[idx + 1] = str(port)
        if "--workers" in cmd:
            idx = cmd.index("--workers")
            if idx + 1 < len(cmd):
                cmd[idx + 1] = str(workers)

    print(f"[ENTRYPOINT] Démarrage de l'application sur le port {port} : {' '.join(cmd)}")
    sys.stdout.flush()
    os.execvp(cmd[0], cmd)

if __name__ == "__main__":
    main()

