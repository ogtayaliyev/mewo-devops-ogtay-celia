# Retro Arcade Leaderboard

Projet DevOps : une petite API de classement pour des jeux d'arcade (Pac-Man, Tetris, Snake, Breakout, Donkey Kong).

Projet réalisés en **Python + FastAPI**, avec **SQLite** pour garder les scores, le tout dans **Docker**. **Prometheus**, **Grafana** et **Alertmanager** sont egalement installer sur le docker pour le monitoring.

[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=ogtayaliyev_mewo-devops-ogtay-celia&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=ogtayaliyev_mewo-devops-ogtay-celia)

Repo : https://github.com/ogtayaliyev/mewo-devops-ogtay-celia

## Le projet

Un back-office de scores. Un joueur envoie son score, l'API vérifie qu'il ne triche pas, et le classement est mis à jour.

Les règles anti-triche :
- le jeu doit exister (pacman, tetris, snake, breakout, donkeykong)
- le score doit être positif
- le score ne doit pas dépasser le max du jeu (ex: pacman max = 999 999)
- il faut attendre 2 secondes entre deux envois du même joueur sur le même jeu

Les scores max par jeu :
- pacman → 999 999
- tetris → 9 999 999
- snake → 99 999
- breakout → 896 980
- donkeykong → 1 247 700

## URLs

- **API / Swagger** : http://localhost:8000/docs
- **Prometheus** : http://localhost:9090
- **Grafana** : http://localhost:3000 → login `admin` / mdp `admin`
- **Alertmanager** : http://localhost:9093


## Routes

- `POST /scores` → envoyer un score `{ "player": "AAA", "game": "pacman", "score": 123456 }`
- `GET /leaderboard/pacman?limit=10` → top 10 du jeu
- `GET /players/AAA` → meilleurs scores du joueur
- `GET /games` → liste des jeux + score max
- `GET /health` → check que l'API répond
- `GET /metrics` → métriques Prometheus

Exemple
```bash
curl -X POST http://localhost:8000/scores -H "Content-Type: application/json" -d "{\"player\":\"AAA\",\"game\":\"pacman\",\"score\":123456}"
curl http://localhost:8000/leaderboard/pacman
```

## Versions 

> **Dev** : code monté en volume, rechargement automatique à la modification d'un fichier


> **Prod** : image Docker figée, `restart: unless-stopped`

## Architecture du code

```
app/
  main.py                 → les routes FastAPI
  games.py                → la logique métier (validation, cooldown, tri)
  db.py                   → SQLite (scores + dernier envoi par joueur/jeu)
  metrics.py              → compteurs Prometheus
  middleware.py           → mesure chaque requête HTTP (latence, status code)
monitoring/               → config Prometheus, Grafana, alertes
scripts/                  → test de charge
```

## Utilisation

### 1. Clonage du projet

```powershell
git clone https://github.com/Freya-Tenebrae/MEWO_dev_ops.git
cd MEWO_dev_ops
```

### 2. Build du projet

> Version Dev
```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d
```

> Version Prod
```powershell
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
```

Apres une petite minute 4 conteneurs sont UP : `api`, `prometheus`, `grafana`, `alertmanager`.

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml ps
```

### 3. Arrêter / relancer le projet

> Version Dev
```powershell
# Arrêter
docker compose -f docker-compose.yml -f docker-compose.dev.yml down

# Relancer
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

> Version Prod
```powershell
# Arrêter
docker compose -f docker-compose.yml -f docker-compose.prod.yml down

# Relancer
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Le monitoring

L'API expose `/metrics` au format Prometheus. À chaque requête, le middleware enregistre :
- combien de requêtes passent (par route et code HTTP)
- la latence (histogramme, pour calculer le p95)
- les scores acceptés (par jeu)
- les scores rejetés (par jeu + motif : score_too_high, cooldown, etc.)
- les consultations de classement

**Prometheus** scrape `/metrics` toutes les 15 secondes.

**Grafana** affiche un dashboard avec le trafic, la latence p95, le taux d'erreur 5xx, et un panneau "tentatives de triche".

**Alertmanager** reçoit les alertes définies dans `monitoring/alerts.yml` :
- **ServiceDown** → l'API ne répond plus
- **HighLatency** → p95 > 500 ms
- **HighErrorRate** → trop de 5xx
- **CheatSpike** → 3 scores rejetés ou plus en 1 minute

### Test ServiceDown
```bash
docker compose stop api
# attendre ~30 sec → voir l'alerte sur http://localhost:9090/alerts
docker compose start api
```

### Test CheatSpike
Dans Swagger envoyer plus de 3 fois un score trop haut (`POST /scores`) :
```json
{"player": "HACK1", "game": "pacman", "score": 9999999}
{"player": "HACK2", "game": "pacman", "score": 9999999}
{"player": "HACK3", "game": "pacman", "score": 9999999}
{"player": "HACK4", "game": "pacman", "score": 9999999}
// ...
```
Apres quelque temps l'alerte **CheatSpike** passe en Firing sur http://localhost:9090/alerts

### Test de charge k6

Il se fait via le script : `scripts/load_test.js` en suivant les etapes suivantes : 

- montée progressive : 5 → 25 → 50 utilisateurs virtuels (ramp-up)
- `POST /scores` (scores valides + ~40 % invalides pour simuler la triche)
- `GET /leaderboard/{game}` (consultation des classements)
- observable dans Grafana (trafic, latence p95) et déclenche **CheatSpike** dans Prometheus

#### Installer k6 (Windows)

Télécharger k6 via https://k6.io/docs/get-started/installation/ ou sur terminal powershell
```powershell
choco install k6
```

#### Lancer le test

Stack Docker déjà up, puis :
```powershell
k6 run scripts/load_test.js
```

Ou via Docker (sans installer k6) :
```powershell
docker compose --profile loadtest run --rm k6
```

Pendant le test, ouvre Grafana (http://localhost:3000) → dashboard **Retro Arcade Leaderboard**.
Tu verras le trafic et la latence monter. À la fin, vérifie http://localhost:9090/alerts → **CheatSpike** en Firing.

### Résultat du test de charge (captures)

J'ai lancé le test k6 via Docker (`docker compose --profile loadtest run --rm k6`). Voici ce qu'on observe :

**1. Grafana — impact de la charge**

![Dashboard Grafana pendant le test k6](docs/screenshots/grafana-load-test.png)

On voit bien le ramp-up :
- le **trafic HTTP** monte (pic ~300 req/s sur `/leaderboard/{game}`)
- la **latence p95** augmente (~80-90 ms)
- les **tentatives de triche** explosent (scores rejetés `score_too_high`)
- pas d'erreur 5xx → l'API tient la charge

**2. Prometheus — alerte CheatSpike déclenchée**

![Alerte CheatSpike en Firing dans Prometheus](docs/screenshots/prometheus-cheatspike.png)

Pendant le test, l'alerte **CheatSpike** passe en **FIRING** : plus de 3 scores rejetés en 1 minute (en fait des milliers avec k6). Les 3 autres alertes restent inactives, c'est normal.

**3. Alertmanager — notification reçue**

![Alerte CheatSpike dans Alertmanager](docs/screenshots/alertmanager-cheatspike.png)

Prometheus envoie l'alerte à **Alertmanager** qui l'affiche avec le résumé *"Pic de tentatives de triche"*.

> L'alerte retombe en **Inactive** ~1-2 min après la fin du test. Il faut regarder Prometheus **pendant** que k6 tourne, ou garder ces captures pour la démo.

Script Python alternatif (plus simple, sans k6) : `scripts/load_test.py`


### Tests unitaires (logique métier)

```powershell
pip install -r requirements-dev.txt
pytest -v
```

Avec couverture de code en local :
```powershell
pytest tests/ -v --cov=app --cov-report=term-missing
```

### CI GitHub Actions

Pipeline `.github/workflows/ci.yml` à chaque push :

1. install des deps
2. ruff (lint)
3. pytest + couverture (affichée dans les logs CI)
4. bandit (SAST)
5. pip-audit (CVE)
6. build Docker + scan Trivy

### SonarCloud

La couverture et les résultats de tests sont publiés dans la CI via `coverage.xml` et `test-results.xml`, puis importés par le scan SonarCloud déclenché dans GitHub Actions.

https://sonarcloud.io/summary/new_code?id=ogtayaliyev_mewo-devops-ogtay-celia
