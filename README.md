# Reproduire le projet CouchDB

## Prérequis

Python 3.10 ou plus et Docker avec Compose. Exécuter les commandes depuis la racine du dépôt, sous Ubuntu ou WSL.

## Créer la base et importer les données

Définir vos identifiants locaux, puis démarrer CouchDB :

```bash
export COUCHDB_USER=projet2_admin
read -rsp 'Mot de passe CouchDB : ' COUCHDB_PASSWORD; echo
export COUCHDB_PASSWORD
docker compose up -d
```

Attendre que http://127.0.0.1:5984/ réponde, puis importer le fichier `donnees.json` fourni :

```bash
python3 scripts/couchdb_pipeline.py
```

Le script crée la base `projet2_communes`, importe les 3 102 communes, installe les index et la vue, exécute les trois requêtes et vérifie leurs résultats. Les réponses sont enregistrées dans `results/`. Il peut être relancé sans créer de doublons. Ne pas utiliser l'option Python `-O`, qui désactive les vérifications.

## Reproduire les trois requêtes

Ouvrir http://127.0.0.1:5984/_utils/, se connecter avec les identifiants définis et sélectionner `projet2_communes`.

| Requête | Fichier ou appel | Résultat attendu |
| --- | --- | --- |
| Filtre multicritère avec projection | Copier `couchdb/requetes/01_filtre.json` dans Mango Query, puis Run Query | 40 communes |
| Tri avec limite | Copier `couchdb/requetes/02_tri.json` dans Mango Query, puis Run Query | 10 communes, Lille en tête |
| Regroupement avec calcul | `GET /projet2_communes/_design/statistiques/_view/population_par_departement?group=true` | 4 départements avec statistiques de population |

Pour afficher les 40 communes dans Fauxton, choisir 50 documents par page. Avec 20 par page, « Results returned: 21 » sert à détecter une page suivante et ne représente pas le total.

Les index sont définis dans `couchdb/indexes.json` et la vue MapReduce dans `couchdb/requetes/vue_departements.json`. Le script les installe automatiquement. Les résultats complets sont dans `results/01_filtre.json`, `results/02_tri.json` et `results/03_regroupement.json`.

## Scripts de préparation

Pour régénérer le JSON depuis le CSV brut, sans refaire l'extraction :

```bash
python3 scripts/transform_communes.py
```

Pour refaire l'extraction HTML dans un nouveau fichier, sans écraser le CSV fourni :

```bash
python3 -m pip install -r requirements.txt
python3 scripts/scrape_communes.py --output data/raw/communes_nouvelle_extraction.csv
```

La base contient 3 102 communes et 3 documents techniques (`_design`), soit 3 105 documents au total. `docker compose stop` arrête CouchDB en conservant les données. Ne pas inclure de mot de passe dans la remise.