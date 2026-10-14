# Projet 2 — Collecter et exploiter des données Web
Dépôt : https://github.com/Bern1408/projet2-ExploTechno
## Membres de l'équipe
- Alexandre Doe-Langevein
- Bernardo Gonçalves da Cruz
## Nettoyage des données
Les étapes 4 à 7 sont réalisées et documentées dans [docs/etapes-4-7.md](docs/etapes-4-7.md).
Le CSV brut contient 3 102 communes. Le nettoyage produit 3 102 documents distincts dans [donnees.json](donnees.json), sans modifier le CSV.
## Structure des documents
Voir [la modélisation](docs/modelisation.md) et [deux exemples complets](docs/exemples.json).
## Modèle d'importation
Base : `projet2_communes`. Importation par lots de 500 avec vérification de chaque réponse; les révisions existantes permettent de relancer l'importation.
## Requêtes
Les deux requêtes Mango, les index et la vue MapReduce sont dans `couchdb/`. Les réponses réellement obtenues et leurs vérifications sont dans `results/`.

## Reproduire les étapes 4 à 7

Prérequis : Python 3.10 ou plus et Docker Desktop démarré avec les conteneurs Linux. Les scripts de transformation et d'importation utilisent seulement la bibliothèque standard Python. `requirements.txt` concerne l'extraction initiale.

Depuis la racine du dépôt, créer un fichier local `.env` avec un identifiant et un mot de passe de votre choix :

```dotenv
COUCHDB_USER=projet2_admin
COUCHDB_PASSWORD=REMPLACER_PAR_UN_MOT_DE_PASSE_LOCAL
```

Ce fichier est ignoré par Git. Ne pas le joindre à la remise. Dans PowerShell :

```powershell
./scripts/reproduire.ps1
# Si nécessaire, préciser le chemin de Python :
# ./scripts/reproduire.ps1 -Python 'C:/chemin/python.exe'
```

La commande démarre CouchDB 3.5.0, transforme les CSV, crée la base, importe les documents, crée les index et la vue, exécute les trois requêtes et compare leurs résultats au JSON. Aucun scraping n'est nécessaire. Pour recréer uniquement la base à partir du JSON déjà fourni, charger les variables du fichier `.env` dans l'environnement puis lancer `python scripts/couchdb_pipeline.py` après `docker compose up -d`.

Pour utiliser un serveur existant, définir `COUCHDB_URL`, `COUCHDB_USER`, `COUCHDB_PASSWORD` et éventuellement `COUCHDB_DATABASE`, puis lancer `python scripts/couchdb_pipeline.py`. Utiliser une base dédiée : la vérification refuse des documents de données étrangers. Ne pas lancer Python avec `-O`, car les vérifications utilisent `assert`.

Interface Fauxton : http://127.0.0.1:5984/_utils/ (identifiants dans votre `.env`). Les données persistent dans le volume Docker. `docker compose stop` arrête le service en conservant les données. Les documents `_design` sont techniques : les 3 102 communes sont comptées séparément.

Le regroupement se consulte par `GET /projet2_communes/_design/statistiques/_view/population_par_departement?group=true`. Les fichiers `01_filtre.json` et `02_tri.json` sont les corps de `POST /projet2_communes/_find`; `indexes.json` contient les corps à envoyer à `POST /projet2_communes/_index`.
## Contribution des membres
- **Bernardo :** Étapes 1-3 et 8
- **Alexandre :** Étapes 4-7

## IA et attribution

Codex a aidé à sélectionner les sources, écrire les scripts, exécuter l’extraction et vérifier les fichiers depuis le terminal.
Pour les étapes 4 à 7, Codex a également préparé la modélisation, le nettoyage, l'importation et les requêtes. Les 3 102 documents et les résultats des trois requêtes ont été comparés automatiquement aux données JSON, dans CouchDB 3.5.0. Chaque membre doit relire et pouvoir expliquer sa contribution.

## Source
[Wikipédia](https://fr.wikipedia.org/wiki/Wikipédia:Citation_et_réutilisation_du_contenu_de_Wikipédia)
