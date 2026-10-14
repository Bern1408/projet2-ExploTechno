# Étapes 4 à 7 - Résultats vérifiés

## Étape 4 : structure

Le modèle est défini dans [modelisation.md](modelisation.md). Un document représente une commune; son identifiant est `commune:<code_insee>`. Les exemples complets suivants illustrent les tableaux, les nombres et les accents.

```json
[
  {
    "_id": "commune:59350",
    "type": "commune",
    "code_insee": "59350",
    "nom": "Lille",
    "departement": "Nord",
    "codes_postaux": [
      "59000",
      "59160",
      "59260",
      "59777",
      "59800"
    ],
    "arrondissement": "Lille",
    "cantons": [
      "Lille-1",
      "Lille-2",
      "Lille-3",
      "Lille-4",
      "Lille-5",
      "Lille-6"
    ],
    "intercommunalite": "Métropole européenne de Lille",
    "superficie_km2": 34.83,
    "population": 238246,
    "annee_population": 2023,
    "densite_hab_km2": 6840.0,
    "source": {
      "url_liste": "https://fr.wikipedia.org/wiki/Liste_des_communes_du_Nord",
      "url_commune": "https://fr.wikipedia.org/wiki/Lille"
    }
  },
  {
    "_id": "commune:02001",
    "type": "commune",
    "code_insee": "02001",
    "nom": "Abbécourt",
    "departement": "Aisne",
    "codes_postaux": [
      "02300"
    ],
    "arrondissement": "Laon",
    "cantons": [
      "Chauny"
    ],
    "intercommunalite": "CA Chauny-Tergnier-La Fère",
    "superficie_km2": 5.96,
    "population": 518,
    "annee_population": 2023,
    "densite_hab_km2": 87.0,
    "source": {
      "url_liste": "https://fr.wikipedia.org/wiki/Liste_des_communes_de_l%27Aisne",
      "url_commune": "https://fr.wikipedia.org/wiki/Abbécourt"
    }
  }
]
```

## Étape 5 : nettoyage

Les 3 102 enregistrements CSV donnent 3 102 communes distinctes, donc aucun doublon retiré. Les doublons identiques seraient fusionnés par code INSEE; des doublons contradictoires provoqueraient une erreur pour éviter une perte silencieuse. Le fichier brut est préservé (empreinte SHA-256 vérifiée).

Les espaces superflus, insécables et sauts de ligne sont normalisés; les textes sont en Unicode NFC. La mention « (préfecture) » est retirée du nom. Les annotations entre crochets sont supprimées. Les virgules décimales deviennent des points et les séparateurs de milliers sont retirés. La population et son année sont séparées. Les codes postaux et cantons deviennent des tableaux sans répétitions. Les valeurs numériques invalides provoquent une erreur; une absence numérique reste `null`.

Une commune a des codes postaux et cantons absents (`[]`), ainsi qu'un arrondissement et une intercommunalité absents (`null`). Aucune population, superficie ou densité n'est manquante. Le détail des comptes et l'empreinte du CSV sont dans `results/nettoyage.json`.

## Étape 6 : importation et vérification

La base `projet2_communes` a été créée dans CouchDB 3.5.0 avec Docker Compose. Le script `scripts/couchdb_pipeline.py` importe `donnees.json` via `_bulk_docs` par lots de 500 et contrôle chaque résultat, car une réponse HTTP réussie ne garantit pas la réussite de tous les documents. Il récupère les révisions avant une nouvelle importation.

Le contrôle relit tous les documents et compare les identifiants, les contenus et les types Python issus du JSON. Les accents et les zéros initiaux sont ainsi contrôlés sur l'ensemble des données. La base contient 3 102 communes et trois documents techniques `_design` (deux index Mango et une vue). Le compteur global CouchDB inclut ces documents techniques et vaut donc 3 105. La procédure PowerShell complète a été exécutée puis relancée avec succès sans doublons. Les preuves sont dans `results/verification.json`.

## Étape 7 : trois requêtes

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

Résultat : 40 communes. Extrait de la réponse réelle :

```json
[
  {
    "nom": "Neuville-en-Ferrain",
    "code_insee": "59426",
    "departement": "Nord",
    "population": 10002,
    "densite_hab_km2": 1618.0
  },
  {
    "nom": "Douchy-les-Mines",
    "code_insee": "59179",
    "departement": "Nord",
    "population": 10109,
    "densite_hab_km2": 1099.0
  },
  {
    "nom": "Annœullin",
    "code_insee": "59011",
    "departement": "Nord",
    "population": 10847,
    "densite_hab_km2": 1204.0
  }
]
```

Ces communes combinent une population élevée et un tissu urbain dense. La projection ne renvoie que les champs utiles. La limite de 5 000 dépasse la taille du jeu de données, donc aucun résultat n'est tronqué ici. L'index `(type, departement, population)` réduit la recherche; la densité est ensuite filtrée. Le script compare l'ensemble des codes INSEE obtenus au filtre calculé depuis le JSON.

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

| Commune | Département | Population (2023) |
| --- | --- | ---: |
| Lille | Nord | 238 246 |
| Amiens | Somme | 136 449 |
| Tourcoing | Nord | 98 772 |
| Roubaix | Nord | 98 286 |
| Dunkerque | Nord | 86 263 |
| Calais | Pas-de-Calais | 67 571 |
| Villeneuve-d'Ascq | Nord | 62 868 |
| Saint-Quentin | Aisne | 52 813 |
| Valenciennes | Nord | 43 468 |
| Arras | Pas-de-Calais | 42 875 |

Lille arrive en tête, devant Amiens. Ce classement concerne seulement les quatre départements du jeu de données. L'index `(type, population, code_insee)` suit l'ordre du tri; le code INSEE départage les égalités. Toutes les directions sont descendantes, conformément à Mango. Le script compare exactement les dix identifiants et leur ordre au classement du JSON.

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

La fonction map émet le département comme clé et la population comme valeur. Le reduce natif `_stats` calcule `count`, `sum`, `min`, `max` et `sumsqr`. Les populations inconnues seraient exclues plutôt que comptées comme zéro. Ici, toutes les populations sont connues.

| Département | Communes | Population cumulée | Population moyenne par commune (sum/count) |
| --- | ---: | ---: | ---: |
| Aisne | 797 | 523342 | 656.64 |
| Nord | 647 | 2615635 | 4042.71 |
| Pas-de-Calais | 887 | 1457905 | 1643.64 |
| Somme | 771 | 565413 | 733.35 |

Le Nord possède la population cumulée la plus élevée, même si le Pas-de-Calais compte davantage de communes. La moyenne affichée est calculée à partir de `sum/count`, et ne représente pas une densité. Le script compare tous les agrégats, y compris `sumsqr`, aux calculs effectués sur le JSON.

### Index et preuves

Les index reproductibles figurent dans `couchdb/indexes.json`. Les réponses Mango `_explain`, sauvegardées dans `results/indexes_utilises.json`, confirment les index sélectionnés. `allow_fallback: false` empêche un remplacement silencieux par un autre index. Les réponses complètes sont dans `results/01_filtre.json`, `results/02_tri.json` et `results/03_regroupement.json`.

## Références techniques

- [Mango, tri, projection et index](https://docs.couchdb.org/en/stable/api/database/find.html)
- [Introduction aux vues MapReduce](https://docs.couchdb.org/en/stable/ddocs/views/intro.html)

## IA et portée de cette documentation

Codex a aidé à produire les scripts et la documentation. Les vérifications ont été exécutées sur une véritable instance CouchDB, puis la procédure complète a été relancée. Ce document couvre les étapes 4 à 7; l'équipe peut l'utiliser pour compléter le rapport de l'étape 8, notamment les contributions et pourcentages réels, qui ne sont pas inventés ici.
