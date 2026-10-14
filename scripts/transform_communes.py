"""CSV brut -> documents JSON; bibliothèque standard uniquement."""
import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def text(value):
    value = re.sub(r"\[[^\]]*\]", "", value)
    value = " ".join(unicodedata.normalize("NFC", value).split())
    return value or None


def number(value, integer=False):
    value = text(value)
    if value is None or value in {"—", "-", "N/A"}:
        return None
    value = value.replace(" ", "").replace(",", ".")
    if not re.fullmatch(r"\d+(?:\.\d+)?", value):
        raise ValueError(f"Nombre invalide: {value!r}")
    if integer and "." in value:
        raise ValueError(f"Entier attendu: {value!r}")
    return int(value) if integer else float(value)


def transform(row):
    code = text(row["code_insee"])
    if not code or not re.fullmatch(r"\d{5}", code):
        raise ValueError("Code INSEE invalide")
    population = text(row["population"])
    match = re.fullmatch(r"([\d ]+) \((\d{4})\)", population or "")
    if population and not match:
        raise ValueError(f"Population invalide: {population}")
    postal = list(dict.fromkeys(re.findall(r"\b\d{5}\b", row["codes_postaux"])))
    if text(row["codes_postaux"]) and not postal:
        raise ValueError("Code postal invalide")
    return {
        "_id": f"commune:{code}", "type": "commune", "code_insee": code,
        "nom": text(re.sub(r"\s*\(préfecture\)\s*", "", row["nom"])),
        "departement": text(row["departement"]), "codes_postaux": postal,
        "arrondissement": text(row["arrondissement"]),
        "cantons": list(dict.fromkeys(filter(None, (text(v) for v in row["canton"].splitlines())))),
        "intercommunalite": text(row["intercommunalite"]),
        "superficie_km2": number(row["superficie_km2"]),
        "population": number(match[1], True) if match else None,
        "annee_population": int(match[2]) if match else None,
        "densite_hab_km2": number(row["densite_hab_km2"]),
        "source": {"url_liste": text(row["url_source"]), "url_commune": text(row["url_commune"])},
    }


def main():
    source = ROOT / "data/raw/communes.csv"
    original_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    with source.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    unique = {}
    for line, row in enumerate(rows, 2):
        try:
            doc = transform(row)
        except ValueError as error:
            raise ValueError(f"Enregistrement {line}: {error}") from error
        if doc["_id"] in unique and unique[doc["_id"]] != doc:
            raise ValueError(f"Doublon contradictoire: {doc['_id']}")
        unique[doc["_id"]] = doc
    docs = sorted(unique.values(), key=lambda d: d["_id"])
    if len(docs) < 2500:
        raise ValueError("Moins de 2 500 communes distinctes")
    write_json(ROOT / "donnees.json", docs)
    write_json(ROOT / "results/nettoyage.json", {
        "csv_sha256": original_hash, "avant": len(rows), "apres": len(docs),
        "doublons_retires": len(rows) - len(docs),
        "departements": dict(Counter(d["departement"] for d in docs)),
        "valeurs_manquantes": {k: sum(d[k] is None or d[k] == [] for d in docs) for k in docs[0]},
    })
    assert hashlib.sha256(source.read_bytes()).hexdigest() == original_hash
    print(f"{len(rows)} lignes -> {len(docs)} documents; CSV brut inchangé")


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
