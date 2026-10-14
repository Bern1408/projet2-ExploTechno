"""Importation idempotente, index, requêtes et vérifications réelles de CouchDB."""
import base64
import json
import os
from collections import defaultdict
from urllib.error import HTTPError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen

from transform_communes import ROOT, write_json


def main():
    base = os.environ.get("COUCHDB_URL", "http://127.0.0.1:5984").rstrip("/")
    database = os.environ.get("COUCHDB_DATABASE", "projet2_communes")
    user, password = os.environ["COUCHDB_USER"], os.environ["COUCHDB_PASSWORD"]
    if urlsplit(base).username or urlsplit(base).password:
        raise ValueError("Utiliser les variables d'environnement pour les identifiants")
    token = base64.b64encode(f"{user}:{password}".encode()).decode()

    def request(method, path, body=None, accepted=()):
        data = json.dumps(body, ensure_ascii=False, allow_nan=False).encode("utf-8") if body is not None else None
        req = Request(base + path, data=data, method=method,
                      headers={"Authorization": "Basic " + token, "Content-Type": "application/json"})
        try:
            with urlopen(req, timeout=120) as response:
                return json.load(response)
        except HTTPError as error:
            if error.code in accepted:
                return None
            raise RuntimeError(f"CouchDB: HTTP {error.code} pour {method} {path}") from None

    def load(relative):
        return json.loads((ROOT / relative).read_text(encoding="utf-8"))

    docs = load("donnees.json")
    if len(docs) < 2500 or len({d['_id'] for d in docs}) != len(docs):
        raise ValueError("Volume ou identifiants invalides")
    db = "/" + quote(database, safe="")
    version = request("GET", "/")["version"]
    request("PUT", db, accepted=(412,))
    # Lire les révisions pour permettre une deuxième importation sans conflits.
    existing = request("POST", db + "/_all_docs", {"keys": [d['_id'] for d in docs]})
    revisions = {r['key']: r['value']['rev'] for r in existing['rows'] if 'value' in r}
    for start in range(0, len(docs), 500):
        batch = [dict(d, **({"_rev": revisions[d['_id']]} if d['_id'] in revisions else {})) for d in docs[start:start + 500]]
        response = request("POST", db + "/_bulk_docs", {"docs": batch})
        if len(response) != len(batch) or any('error' in r for r in response):
            raise RuntimeError("Importation partielle: " + json.dumps(response))
    for index in load("couchdb/indexes.json"):
        request("POST", db + "/_index", index)
    view = load("couchdb/vue_departements.json")
    old = request("GET", db + "/_design/statistiques", accepted=(404,))
    if old:
        view['_rev'] = old['_rev']
    request("PUT", db + "/_design/statistiques", view)

    # Comparaison intégrale: nombre, contenu, types, accents et absence de documents étrangers.
    actual = request("GET", db + "/_all_docs?include_docs=true")
    actual = {r['id']: r['doc'] for r in actual['rows'] if not r['id'].startswith('_design/')}
    assert set(actual) == {d['_id'] for d in docs}, "Nombre ou identifiants incorrects"
    for doc in docs:
        stored = dict(actual[doc['_id']])
        stored.pop('_rev', None)
        assert stored == doc, f"Contenu incorrect: {doc['_id']}"
        for field in doc:
            assert type(stored[field]) is type(doc[field]), f"Type incorrect: {field}"
    results = {}
    explanations = {}
    for name in ('01_filtre', '02_tri'):
        query = load(f"couchdb/requetes/{name}.json")
        results[name] = request("POST", db + "/_find", query)
        assert 'warning' not in results[name], "Index non utilisé"
        explanations[name] = request("POST", db + "/_explain", query)
        assert explanations[name]['index']['name'] == query['use_index'][1]
        write_json(ROOT / f"results/{name}.json", results[name])
    expected_filter = [d for d in docs if d['departement'] == 'Nord' and d['population'] is not None and d['population'] >= 10000 and d['densite_hab_km2'] is not None and d['densite_hab_km2'] >= 1000]
    assert {d['code_insee'] for d in results['01_filtre']['docs']} == {d['code_insee'] for d in expected_filter}
    expected_top = sorted((d for d in docs if d['population'] is not None), key=lambda d: (d['population'], d['code_insee']), reverse=True)[:10]
    assert [d['code_insee'] for d in results['02_tri']['docs']] == [d['code_insee'] for d in expected_top]
    stats = request("GET", db + "/_design/statistiques/_view/population_par_departement?group=true")
    populations = defaultdict(list)
    for doc in docs:
        if doc['population'] is not None:
            populations[doc['departement']].append(doc['population'])
    assert {r['key'] for r in stats['rows']} == set(populations)
    for row in stats['rows']:
        numbers = populations[row['key']]
        assert row['value'] == {"sum": sum(numbers), "count": len(numbers), "min": min(numbers), "max": max(numbers), "sumsqr": sum(n*n for n in numbers)}
    write_json(ROOT / "results/03_regroupement.json", stats)
    write_json(ROOT / "results/indexes_utilises.json", explanations)
    write_json(ROOT / "results/verification.json", {
        "couchdb_version": version, "base": database, "documents_communes": len(actual),
        "documents_design": request("GET", db)['doc_count'] - len(actual),
        "contenu_integral_types_accents": "validés sur tous les documents",
        "requetes_comparees_au_json": True, "filtre_resultats": len(expected_filter),
        "tri_resultats": len(expected_top), "groupes": len(stats['rows']),
    })
    print(f"Base {database}: {len(actual)} communes vérifiées; trois requêtes validées")


if __name__ == "__main__":
    main()
