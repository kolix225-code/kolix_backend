# scripts/migrate_supabase.py
"""
Script utilitaire pour valider la connexion Supabase et exécuter les migrations Alembic.
Usage:
    python scripts/migrate_supabase.py "postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres" [--seed]
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

# Racinedu projet
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))


def clean_supabase_url(raw_url: str) -> str:
    """Nettoie et formate l'URL Supabase pour asyncpg."""
    url = raw_url.strip()
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    if "sslmode=require" in url:
        url = url.replace("sslmode=require", "ssl=require")

    return url


def main():
    parser = argparse.ArgumentParser(description="Migration et initialisation Supabase pour Kolix")
    parser.add_argument("db_url", nargs="?", default=os.getenv("DATABASE_URL"), help="URL de connexion Supabase")
    parser.add_argument("--seed", action="store_true", help="Insérer les données initiales de démo/admin")
    args = parser.parse_args()

    raw_url = args.db_url
    if not raw_url:
        print("[ERREUR] Aucune URL Supabase fournie.")
        print("Usage: python scripts/migrate_supabase.py \"postgresql://postgres:pass@db.ref.supabase.co:5432/postgres\"")
        print("Ou définissez la variable d'environnement DATABASE_URL.")
        sys.exit(1)

    formatted_url = clean_supabase_url(raw_url)
    os.environ["DATABASE_URL"] = formatted_url

    print("=" * 70)
    print("  KOLIX BACKEND - MIGRATION & INITIALISATION SUPABASE")
    print("=" * 70)

    parsed = urlparse(formatted_url.replace("postgresql+asyncpg://", "http://"))
    print(f"-> Hôte Supabase : {parsed.hostname}")
    print(f"-> Port          : {parsed.port or 5432}")
    print(f"-> Base de données : {parsed.path.lstrip('/')}")
    print(f"-> Utilisateur   : {parsed.username}")

    print("\n[1/2] Exécution des migrations Alembic (alembic upgrade head)...")
    res = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=str(ROOT_DIR))

    if res.returncode != 0:
        print("\n[ERREUR] La migration Alembic a échoué.")
        print("Vérifiez le mot de passe, l'accès réseau ou le pare-feu Supabase.")
        sys.exit(res.returncode)

    print("\n[OK] Toutes les tables et colonnes ont été créées sur Supabase !")

    if args.seed:
        print("\n[2/2] Insertion des données initiales (scripts/seed.py)...")
        res_seed = subprocess.run([sys.executable, "scripts/seed.py"], cwd=str(ROOT_DIR))
        if res_seed.returncode == 0:
            print("[OK] Données de démonstration et compte administrateur insérés avec succès.")
        else:
            print("[ATTENTION] L'insertion des données a rencontré une anomalie.")
    else:
        print("\n[NOTE] Pour insérer des données initiales (admin, boutiques test), ajoutez l'option --seed.")

    print("\n" + "=" * 70)
    print("  CONFIGURATION SUPABASE TERMINÉE AVEC SUCCÈS !")
    print("=" * 70)


if __name__ == "__main__":
    main()
