# Étape 4 - Modélisation

Un document représente une commune française, identifiée par son code INSEE. Les questions visées sont : quelles communes du Nord sont grandes et denses, quelles sont les dix communes les plus peuplées du jeu de données, et quelle est la population cumulée par département ?

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

JSON possède un type `number`; les entiers et décimaux sont sérialisés respectivement comme `518` et `5.96`. Une valeur inconnue est `null`, jamais automatiquement zéro. Pour un champ multivalué, l'absence est `[]`. Les années sont des entiers; aucune date complète n'est extraite. Une éventuelle date complète utiliserait `YYYY-MM-DD`.

Les mesures et informations administratives sont généralement consultées avec la commune : elles restent dans le même document pour éviter les jointures. Le modèle principalement plat simplifie les index Mango. Les URLs sont regroupées dans `source`; les codes postaux et les cantons sont des tableaux plutôt que des textes contenant des sauts de ligne. La densité publiée est conservée : un recalcul population/superficie pourrait diverger par arrondi.

Deux exemples complets figurent dans [exemples.json](exemples.json) : Lille (`commune:59350`), avec plusieurs codes postaux et cantons, et Abbécourt (`commune:02001`), qui illustre les accents et les zéros initiaux. `_rev` est géré par CouchDB et n'est pas inclus dans le fichier à importer. Le code INSEE convient à ce relevé; des fusions ou changements administratifs futurs nécessiteraient une gestion historique supplémentaire.
