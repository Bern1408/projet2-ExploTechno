# Projet 2 - Communes et CouchDB

Dépôt : https://github.com/Bern1408/projet2-ExploTechno

## Remise

Le [rapport](rapport.md) regroupe la modélisation, deux exemples, le nettoyage, l'importation, les requêtes et leur interprétation. Les membres doivent compléter leurs pourcentages réels de participation avant la remise.

- `data/raw/communes.csv` : extraction HTML brute UTF-8, inchangée.
- `donnees.json` : 3 102 communes distinctes nettoyées.
- `scripts/` : extraction, transformation et importation avec vérifications.
- `couchdb/` : configuration, index, deux requêtes Mango et vue MapReduce.
- `results/` : résultats réellement obtenus et preuves des vérifications.
- `compose.yaml` : instance CouchDB reproductible avec volume persistant.
- `requirements.txt` : dépendances de l'extraction HTML.

## Recréer la base sous Ubuntu / WSL

Prérequis : Python 3.10 ou plus et Docker avec Compose. Les scripts de nettoyage et d'importation utilisent uniquement la bibliothèque standard Python. Il n'est pas nécessaire de refaire l'extraction.

Définir localement vos identifiants dans le terminal (aucun mot de passe à déposer dans Git ou dans le ZIP) :

```bash
export COUCHDB_USER=projet2_admin
read -rsp 'Mot de passe CouchDB : ' COUCHDB_PASSWORD; echo
export COUCHDB_PASSWORD
docker compose up -d
```

Attendre que CouchDB réponde sur http://127.0.0.1:5984/, puis :

```bash
# Facultatif : régénérer le JSON à partir du CSV brut.
python3 scripts/transform_communes.py
# Créer la base, importer le JSON fourni et reproduire les résultats.
python3 scripts/couchdb_pipeline.py
```

Résultat attendu : `Base projet2_communes: 3102 communes vérifiées; trois requêtes validées`. Une deuxième exécution ne crée pas de doublons. Les 3 documents `_design` sont techniques : CouchDB affiche donc 3 105 documents au total.

Pour un serveur existant, définir `COUCHDB_URL` et éventuellement `COUCHDB_DATABASE` en plus des identifiants. Utiliser une base dédiée. Ne pas lancer Python avec `-O`, car les vérifications utilisent `assert`. Les paramètres par défaut sont `http://127.0.0.1:5984` et `projet2_communes`.

Pour refaire l'extraction seulement : installer `requirements.txt` avec pip puis lancer `scripts/scrape_communes.py --output` avec un nouveau chemin afin de préserver le CSV fourni.

## Consulter les requêtes dans Fauxton

Ouvrir http://127.0.0.1:5984/_utils/ et la base `projet2_communes`.

- Copier `couchdb/requetes/01_filtre.json` dans Mango Query : 40 communes.
- Copier `couchdb/requetes/02_tri.json` : 10 communes, Lille en tête.
- Consulter `GET /projet2_communes/_design/statistiques/_view/population_par_departement?group=true` : 4 départements.

Choisir 50 documents par page pour afficher tout le filtre. Avec 20 par page, Fauxton demande 21 résultats pour détecter une page suivante; ce compteur ne représente pas le total.

Les fichiers de `couchdb/indexes.json` sont envoyés à `POST /projet2_communes/_index`. La vue `couchdb/requetes/vue_departements.json` est envoyée à `PUT /projet2_communes/_design/statistiques`. Le script effectue ces opérations automatiquement.

`docker compose stop` arrête le service en conservant les données. Pour le ZIP, inclure les fichiers suivis par Git, sans `.git`, identifiants ni caches.
