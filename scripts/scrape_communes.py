"""Extraction HTML -> CSV bruts. Aucun nettoyage des valeurs extraites."""
import argparse
import csv
import re
import time
from pathlib import Path
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
USER_AGENT = "Projet2CouchDB/1.0 (+https://github.com/Bern1408/projet2-ExploTechno; educational HTML extraction)"
SOURCES = [
    ("Nord", "nord", "https://fr.wikipedia.org/wiki/Liste_des_communes_du_Nord"),
    ("Pas-de-Calais", "pas-de-calais", "https://fr.wikipedia.org/wiki/Liste_des_communes_du_Pas-de-Calais"),
    ("Somme", "somme", "https://fr.wikipedia.org/wiki/Liste_des_communes_de_la_Somme"),
    ("Aisne", "aisne", "https://fr.wikipedia.org/wiki/Liste_des_communes_de_l%27Aisne"),
]
FIELDS = ["nom", "code_insee", "codes_postaux", "arrondissement", "canton",
          "intercommunalite", "superficie_km2", "population", "densite_hab_km2",
          "departement", "url_source", "url_commune"]


def extract(html, department, source_url):
    soup = BeautifulSoup(html, "html.parser")
    candidates = []
    for table in soup.select("table.wikitable"):
        first = table.find("tr")
        if first is None:
            continue
        headers = [" ".join(c.get_text(" ", strip=True).split()).lower()
                   for c in first.find_all(["th", "td"], recursive=False)]
        if len(headers) >= 9 and "insee" in headers[1] and "superficie" in headers[6] and "population" in headers[7]:
            candidates.append(table)
    if len(candidates) != 1:
        raise ValueError(f"{department}: tableau des communes ambigu ou introuvable")
    rows = []
    for tr in candidates[0].find_all("tr"):
        cells = tr.find_all(["td", "th"], recursive=False)
        if len(cells) < 9:
            continue
        # Ce controle identifie les lignes de donnees sans changer les valeurs stockees.
        if not re.fullmatch(r"\d{5}", cells[1].get_text().strip()):
            continue
        link = cells[0].find("a", href=True)
        if link is None:
            raise ValueError(f"{department}: URL de commune manquante")
        values = []
        for cell in cells[:9]:
            # Conserver les sauts de ligne visibles (<br>) et les espaces, accents,
            # virgules decimales, annotations et annees avant tout nettoyage.
            for br in cell.find_all("br"):
                br.replace_with("\n")
            values.append(cell.get_text(separator="", strip=False))
        row = dict(zip(FIELDS[:9], values))
        row.update(departement=department, url_source=source_url,
                   url_commune=urljoin(source_url, link["href"]))
        rows.append(row)
    if len(rows) < 500:
        raise ValueError(f"{department}: volume inattendu ({len(rows)} lignes)")
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", type=int, help="Extraire N communes du Nord pour un test")
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "raw" / "communes.csv")
    parser.add_argument("--delay", type=float, default=3, help="Pause entre requetes (secondes)")
    args = parser.parse_args()
    if args.sample is not None and args.sample < 1:
        parser.error("--sample doit etre positif")
    if args.delay < 3:
        parser.error("--delay doit etre au moins 3 secondes")
    output = args.output.resolve()
    if output.exists():
        parser.error("Le fichier existe deja. Choisir un nouveau --output pour preserver les CSV bruts.")
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    response = session.get("https://fr.wikipedia.org/robots.txt", timeout=60)
    response.raise_for_status()
    robots = RobotFileParser()
    robots.parse(response.text.splitlines())
    delay = max(args.delay, robots.crawl_delay(USER_AGENT) or 0, robots.crawl_delay("*") or 0)
    sources = SOURCES[:1] if args.sample else SOURCES
    if any(not robots.can_fetch(USER_AGENT, url) for _, _, url in sources):
        raise RuntimeError("Extraction arretee: robots.txt interdit une source")
    all_rows = []
    for department, _, url in sources:
        time.sleep(delay)
        response = session.get(url, timeout=60)
        response.raise_for_status()
        rows = extract(response.content, department, url)
        if args.sample:
            rows = rows[:args.sample]
        all_rows.extend(rows)
        print(f"{department}: {len(rows)} communes, HTTP {response.status_code}", flush=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"Total: {len(all_rows)} communes. CSV UTF-8 brut: {output}")


if __name__ == "__main__":
    main()
