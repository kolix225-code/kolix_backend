# Guide de Déploiement : Render & Base de Données Supabase

Ce guide explique pas à pas comment configurer votre base de données PostgreSQL managée sur **Supabase** et déployer votre API FastAPI sur **Render** avec gestion automatique des branches (`main` pour la production, `ppd` pour la préproduction, et `dev` pour le développement).

---

## 1. Structure des Branches Git

Le dépôt GitHub `https://github.com/kolix225-code/kolix_backend.git` est désormais configuré avec 3 branches :

| Branche | Rôle | Cible de Déploiement Render | URL Type |
| :--- | :--- | :--- | :--- |
| **`main`** | **Production** (version stable, données réelles) | `kolix-backend-prod` | `https://kolix-backend-prod.onrender.com` |
| **`ppd`** | **Préproduction** (staging, validation client) | `kolix-backend-ppd` | `https://kolix-backend-ppd.onrender.com` |
| **`dev`** | **Développement** (tests de nouvelles fonctionnalités) | Local ou environnement dev | `http://localhost:8000` |

---

## 2. Configuration de Supabase (Base de Données PostgreSQL)

### Étape 2.1 : Créer le projet Supabase
1. Rendez-vous sur [https://supabase.com](https://supabase.com) et connectez-vous.
2. Cliquez sur **New Project**.
3. Renseignez les informations :
   - **Name** : `kolix-db-prod` (ou `kolix-db-ppd`)
   - **Database Password** : Définissez un mot de passe robuste et notez-le soigneusement (ex: `KolixSecurPass2026!`).
   - **Region** : Choisissez **Central Europe (Frankfurt)** (`eu-central-1`) ou **West Europe (London/Paris)** pour une faible latence vers l'Afrique de l'Ouest et l'Europe.
   - **Pricing Plan** : Free (ou Pro selon vos besoins).
4. Cliquez sur **Create new project** et attendez 1 à 2 minutes que le provisionnement soit terminé.

---

### Étape 2.2 : Récupérer la chaîne de connexion (`DATABASE_URL`)
1. Dans le tableau de bord Supabase, allez dans **Project Settings** (icône d'engrenage en bas à gauche) > **Database**.
2. Faites défiler jusqu'à la section **Connection parameters** ou **Connection string** :
   - Sélectionnez l'onglet **URI**.
   - Vous avez deux modes :
     - **Session / Direct (Port 5432)** :
       ```text
       postgresql://postgres:[VOTRE-MOT-DE-PASSE]@db.[VOTRE-PROJECT-REF].supabase.co:5432/postgres
       ```
     - **Transaction Pooler (Port 6543)** *(Recommandé pour Render pour éviter de saturer les connexions)* :
       ```text
       postgresql://postgres.[VOTRE-PROJECT-REF]:[VOTRE-MOT-DE-PASSE]@aws-0-eu-central-1.pooler.supabase.com:6543/postgres
       ```
3. Remplacez `[VOTRE-MOT-DE-PASSE]` par le mot de passe réel que vous avez choisi à l'étape 2.1.

---

### Étape 2.3 : Appliquer les tables et migrations sur Supabase

Vous disposez d'un script clé en main dans le projet pour initialiser la base Supabase depuis votre machine :

```powershell
cd C:\Website\kolix_backend

# Exécuter les migrations Alembic sur Supabase
.\.venv\Scripts\python.exe scripts\migrate_supabase.py "postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres"

# Optionnel : Pour insérer aussi les données initiales de démo/admin :
.\.venv\Scripts\python.exe scripts\migrate_supabase.py "postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres" --seed
```

> [!NOTE]
> Le script `scripts/entrypoint.py` exécutera aussi automatiquement `alembic upgrade head` lors de chaque démarrage de conteneur sur Render.

---

## 3. Déploiement sur Render

### Méthode 1 : Déploiement Automatique via Blueprint (Recommandé - 2 minutes)

Le fichier [`render.yaml`](file:///c:/Website/kolix_backend/render.yaml) est déjà prêt à la racine du dépôt.

1. Connectez-vous sur [https://dashboard.render.com](https://dashboard.render.com).
2. Cliquez sur le bouton **New +** en haut à droite > **Blueprint**.
3. Connectez votre compte GitHub et sélectionnez le dépôt **`kolix225-code/kolix_backend`**.
4. Render va détecter le fichier `render.yaml` et proposer de créer les deux services :
   - `kolix-backend-prod` (branche `main`)
   - `kolix-backend-ppd` (branche `ppd`)
5. Dans le formulaire, renseignez la variable **`DATABASE_URL`** pour chacun des deux services avec votre URL Supabase.
6. Cliquez sur **Apply**.
7. Render va construire l'image Docker multi-stage optimisée et démarrer l'API !

---

### Méthode 2 : Création Manuelle d'un Web Service sur Render

Si vous préférez configurer le service manuellement dans l'interface de Render :

1. Dans Render Dashboard, cliquez sur **New +** > **Web Service**.
2. Connectez le dépôt **`kolix225-code/kolix_backend`**.
3. Choisissez la branche :
   - `main` pour la Production
   - `ppd` pour la Préproduction
4. Configurez les options :
   - **Name** : `kolix-backend-prod`
   - **Region** : `Frankfurt (EU Central)`
   - **Runtime** : **Docker**
   - **Dockerfile Path** : `./Dockerfile`
   - **Docker Context** : `.`
   - **Instance Type** : `Free` ou `Starter` ($7/mois sans mise en veille)
5. Dans **Advanced** > **Health Check Path** :
   - Indiquez : `/health`
6. Dans la section **Environment Variables**, ajoutez :
   - `ENVIRONMENT` = `production` (ou `staging`)
   - `DEBUG` = `false`
   - `PORT` = `8000`
   - `DATABASE_URL` = `postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres` (votre URL Supabase)
   - `SECRET_KEY` = *(générez une chaîne aléatoire de 64 caractères)*
   - `BACKEND_CORS_ORIGINS` = `*`
   - `AUTO_SEED` = `false`
7. Cliquez sur **Create Web Service**.

---

## 4. Vérification du Déploiement

Une fois le déploiement terminé sur Render, vous obtiendrez votre URL publique (ex: `https://kolix-backend-prod.onrender.com`).

### 1. Test de santé :
Ouvrez dans votre navigateur ou via terminal :
```bash
curl https://kolix-backend-prod.onrender.com/health
```
Réponse attendue :
```json
{
  "status": "healthy",
  "app": "Kolix Backend API",
  "version": "1.0.0",
  "environment": "production"
}
```

### 2. Documentation Swagger interactive :
Consultez la documentation complète de l'API :
`https://kolix-backend-prod.onrender.com/docs`

---

## 5. Connexion avec le Frontend Kolix

Dans votre projet frontend (`C:\Website\kolix\.env`), mettez à jour la variable `VITE_API_URL` :

```env
# Pour pointer vers la production Render :
VITE_API_URL=https://kolix-backend-prod.onrender.com

# Ou pour pointer vers la préproduction Render :
# VITE_API_URL=https://kolix-backend-ppd.onrender.com
```

Puis rebuildez ou relancez le frontend :
```powershell
cd C:\Website\kolix
npm run build
npm run dev
```
Le frontend consommera désormais directement l'API déployée sur Render connectée à Supabase !
