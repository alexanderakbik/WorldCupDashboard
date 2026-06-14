import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup


BASE_DIR = Path(__file__).resolve().parent
WIKIPEDIA_URL = "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup"


def normalize_name(name):
    name = name.lower()
    name = name.replace("republic", "")
    name = name.replace("czechia", "czech")
    name = name.replace("united states", "usa")
    name = name.replace("bosnia and herzegovina", "bosnia")
    name = name.replace("turkey", "türkiye")
    return name.strip()


def scrape_world_cup_results():
    response = requests.get(
        WIKIPEDIA_URL,
        headers={"User-Agent": "WorldCupDashboard/1.0"},
        timeout=20,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    results = []
    for match in soup.find_all("div", class_="footballbox"):
        home = match.find("th", class_="fhome")
        away = match.find("th", class_="faway")
        score = match.find("th", class_="fscore")
        if not home or not away or not score:
            continue

        score_match = re.fullmatch(r"\s*(\d+)\s*[–-]\s*(\d+)\s*", score.get_text())
        score_a = int(score_match.group(1)) if score_match else None
        score_b = int(score_match.group(2)) if score_match else None
        results.append(
            {
                "teamA": home.get_text(strip=True),
                "teamB": away.get_text(strip=True),
                "scoreA": score_a,
                "scoreB": score_b,
                "played": score_match is not None,
            }
        )

    with (BASE_DIR / "predictions.json").open() as file:
        predictions = json.load(file)

    match_ids = {
        tuple(sorted((normalize_name(p["teamA"]), normalize_name(p["teamB"])))): p["match_id"]
        for p in predictions
    }
    mapped_results = []
    for result in results:
        key = tuple(sorted((normalize_name(result["teamA"]), normalize_name(result["teamB"]))))
        if key in match_ids:
            result["match_id"] = match_ids[key]
            mapped_results.append(result)

    if not mapped_results:
        raise RuntimeError("Wikipedia returned no results matching predictions.json.")
    return mapped_results


def save_results(results, path=BASE_DIR / "real_results.json"):
    with Path(path).open("w") as file:
        json.dump(results, file, indent=2)


if __name__ == "__main__":
    latest_results = scrape_world_cup_results()
    save_results(latest_results)
    print(f"Scraped and mapped {len(latest_results)} matches from Wikipedia.")
