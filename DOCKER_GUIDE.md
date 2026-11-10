# Guide Docker & Déploiement Multi-Environnements — Kolix Backend

Ce guide détaille l'utilisation des conteneurs Docker pour les trois environnements : **Développement (dev)**, **Pré-production (preprod / staging)** et **Déploiement Production (deploy / prod)**, ainsi que la gestion rigoureuse des variables d'environnement.

---

## 🏗️ Structure des Fichiers Docker

```text
C:\Website\kolix_backend\
├── Dockerfile                   # Multi-stage build UV (targets: development, production)
├── .dockerignore                # Exclusions pour builds rapides et légers (< 130 Mo)
├── entrypoint.sh                # Script de démarrage POSIX
├── scripts/
│   └── entrypoint.py            # Logique d'attente DB/Redis, migrations auto et seed
├── nginx/
│   └── conf.d/
│       └── kolix.conf           # Configuration proxy inverse, rate-limiting et compression
│
├── .env.dev                     # Variables pour dev local conteneurisé
├── .env.preprod                 # Variables pour pré-production / staging
├── .env.prod                    # Variables pour production (modèle sécurisé)
│
├── docker-compose.dev.yml       # Stack dev (API bind-mount reload, Postgres 17, Redis 7, MinIO)
├── docker-compose.preprod.yml   # Stack staging (API prod, Worker Arq, DB Staging, Redis auth)
├── docker-compose.prod.yml      # Stack production (Nginx Gateway, 4 Workers, DB optimisée, Isolation réseau)
└── docker-compose.deploy.yml    # Alias de déploiement direct vers la configuration de production
```

---

## 🔒 Gestion des Variables d'Environnement dans Docker

### Règle de Préséance Docker Compose

1. **Variables passées en ligne de commande** (ex: `TAG=v1.0.0 docker compose ...`)
2. **Variables d'environnement de la machine hôte / CI/CD** (GitHub Actions, GitLab CI)
3. **Fichier spécifié par `env_file:`** (`.env.dev`, `.env.preprod`, `.env.prod`)
4. **Valeurs par défaut définies dans le code Python** (`pydantic-settings`)

### Bonnes Pratiques de Sécurité

> [!IMPORTANT]
> - Ne committez **jamais** `.env.prod` contenant des mots de passe réels dans un dépôt public.
> - En production, les conteneurs PostgreSQL et Redis sont placés dans un réseau Docker interne (`kolix-internal-net`) avec `internal: true`. Aucun port de base de données n'est exposé sur l'IP publique de la machine.
> - Seul le reverse-proxy Nginx expose les ports `80` (HTTP) et `443` (HTTPS).

---

## 1. Environnement Développement (`dev`)

Le mode développement utilise le **Bind Mount** : le dossier de code local est monté dans `/app`. Toute modification de code Python déclenche immédiatement le rechargement Uvicorn sans reconstruire l'image.

### Démarrage

```bash
# Lancer la stack complète en tâche de fond avec reconstruction
docker compose -f docker-compose.dev.yml up -d --build

# Visualiser les logs de l'API en direct
docker compose -f docker-compose.dev.yml logs -f api
```

### Services disponibles :
- **FastAPI Swagger Docs** : [http://localhost:8000/docs](http://localhost:8000/docs)
- **MinIO Console UI** : [http://localhost:9001](http://localhost:9001) *(Identifiants: `minio_kolix` / `minio_kolix_secure_key`)*
- **PostgreSQL Local** : `localhost:5432` (`kolix_admin` / `kolix_secure_pass_2026`)
- **Redis Local** : `localhost:6379`

### Arrêt

```bash
docker compose -f docker-compose.dev.yml down
# Pour effacer les volumes de données :
docker compose -f docker-compose.dev.yml down -v
```

---

## 2. Environnement Pré-production / Staging (`preprod`)

Simule fidèlement l'environnement de production avec isolation des données, worker asynchrone Arq actif et vérifications de santé (`healthcheck`).

### Démarrage

```bash
docker compose -f docker-compose.preprod.yml up -d --build
```

### Vérification de l'état des conteneurs :

```bash
docker compose -f docker-compose.preprod.yml ps
```

---

## 3. Déploiement en Production (`deploy` / `prod`)

La stack de production comprend :
1. **Passerelle Nginx** :
   - Limitation de débit contre les attaques DDoS et le spam de commandes (`limit_req` sur `/orders/checkout`).
   - Compression Gzip dynamique.
   - En-têtes de sécurité HSTS, X-Frame-Options, X-Content-Type-Options.
2. **API FastAPI Multi-Workers** :
   - 4 workers ASGI haute performance.
   - Limite de mémoire : 2 Go, réservation : 512 Mo.
3. **Base de Données PostgreSQL 17 Réglée pour la Haute Charge** :
   - Mémoire partagée `shared_buffers=512MB`.
   - Jusqu'à 200 connexions concurrentes.
   - Isolation réseau totale.
4. **Worker Asynchrone Arq** pour les relances WhatsApp et l'envoi d'OTP en tâche de fond.

### Déploiement

```bash
# 1. Vérifier le fichier .env.prod
nano .env.prod

# 2. Lancer le déploiement
docker compose -f docker-compose.deploy.yml up -d --build

# 3. Vérifier la santé du déploiement
docker compose -f docker-compose.deploy.yml ps
curl http://localhost/health
```

---

## 🔄 Commandes Utiles d'Exploitation

### Exécuter manuellement une migration dans le conteneur en cours :

```bash
docker compose -f docker-compose.dev.yml exec api alembic upgrade head
```

### Réinsérer les données de démo dans le conteneur :

```bash
docker compose -f docker-compose.dev.yml exec api python scripts/seed.py
```

### Ouvrir un terminal interactif dans l'API :

```bash
docker compose -f docker-compose.dev.yml exec api bash
```

