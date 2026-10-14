# Projet 2 — Collecter et exploiter des données Web
Dépôt : https://github.com/Bern1408/projet2-ExploTechno
## Membres de l'équipe
- Alexandre Doe-Langevein
- Bernardo Gonçalves da Cruz
## Nettoyage des données
Les 3102 enregistrements CSV donnent des communes distinctes, donc aucun doublon a été retiré.
## Structure des documents
| Champ | Type JSON | Rôle |
| --- | --- | --- |
| `_id` | string | `commune:` suivi du code INSEE, unique et stable pour ce jeu de données |
| `type` | string | Toujours `commune`; distingue les données des documents techniques |
| `code_insee` | string | Cinq caractères, conserve les zéros initiaux |
| `nom`, `departement` | string | Textes normalisés en Unicode NFC |
| `codes_postaux`, `cantons` | array de strings | Plusieurs valeurs possibles; tableau vide si inconnu |
| `arrondissement`, `intercommunalite` | string ou null | Informations administratives |
| `superficie_km2`, `densite_hab_km2` | number ou null | Décimaux, respectivement km² et habitants/km² |
| `population` | number entier ou null | Nombre d'habitants |
| `annee_population` | number entier ou null | Année de référence extraite de la population |
| `source` | object | URLs `url_liste` et `url_commune`, de type string |

## Méthode d'importation
La base `projet2_communes` a été créée dans CouchDB 3.5.0 avec Docker Compose. Le script `scripts/couchdb_pipeline.py` importe `donnees.json` via `_bulk_docs` par lots de 500 et contrôle chaque résultat, car une réponse HTTP réussie ne garantit pas la réussite de tous les documents. Il récupère les révisions avant une nouvelle importation.

Le contrôle relit tous les documents et compare les identifiants, les contenus et les types Python issus du JSON. Les accents et les zéros initiaux sont ainsi contrôlés sur l'ensemble des données. La base contient 3 102 communes et trois documents techniques `_design` (deux index Mango et une vue). Le compteur global CouchDB inclut ces documents techniques et vaut donc 3 105. La procédure PowerShell complète a été exécutée puis relancée avec succès sans doublons. Les preuves sont dans `results/verification.json`.
## Requêtes
### 1. Filtre multicritère avec projection (Mango)

Question : quelles communes du Nord ont au moins 10 000 habitants et une densité d'au moins 1 000 habitants/km² ?

```json
{
  "selector": {
    "type": "commune",
    "departement": "Nord",
    "population": {
      "$gte": 10000
    },
    "densite_hab_km2": {
      "$gte": 1000
    }
  },
  "fields": [
    "nom",
    "code_insee",
    "departement",
    "population",
    "densite_hab_km2"
  ],
  "use_index": [
    "filtre",
    "par_departement_population"
  ],
  "allow_fallback": false,
  "limit": 5000
}
```
### 2. Tri avec limite (Mango)

Question : quelles sont les dix communes les plus peuplées parmi les quatre départements extraits ?

```json
{
  "selector": {
    "type": "commune",
    "population": {
      "$gte": 0
    },
    "code_insee": {
      "$gte": ""
    }
  },
  "fields": [
    "nom",
    "code_insee",
    "departement",
    "population",
    "annee_population"
  ],
  "sort": [
    {
      "type": "desc"
    },
    {
      "population": "desc"
    },
    {
      "code_insee": "desc"
    }
  ],
  "limit": 10,
  "use_index": [
    "classement",
    "par_population"
  ],
  "allow_fallback": false
}
```
### 3. Regroupement avec calcul (vue MapReduce)

Question : combien d'habitants et de communes compte chaque département extrait ?

```json
{
  "_id": "_design/statistiques",
  "language": "javascript",
  "views": {
    "population_par_departement": {
      "map": "function(doc) { if (doc.type === 'commune' && typeof doc.departement === 'string' && typeof doc.population === 'number') { emit(doc.departement, doc.population); } }",
      "reduce": "_stats"
    }
  }
}
```
Appel : `GET /projet2_communes/_design/statistiques/_view/population_par_departement?group=true`.

## Contribution des membres
- **Bernardo :** Étapes 1-3 et 8
- **Alexandre :** Étapes 4-7

## IA et attribution

Codex a aidé à sélectionner les sources, écrire les scripts, exécuter l’extraction et vérifier les fichiers depuis le terminal. Codex a également préparé la modélisation, le nettoyage, l'importation et les requêtes. Les 3 102 documents et les résultats des trois requêtes ont été comparés automatiquement aux données JSON, dans CouchDB 3.5.0.

## Source
[Wikipédia](https://fr.wikipedia.org/wiki/Wikipédia:Citation_et_réutilisation_du_contenu_de_Wikipédia)