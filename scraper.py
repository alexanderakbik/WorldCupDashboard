import json
import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime

def scrape_world_cup_results():
    url = 'https://en.wikipedia.org/wiki/2026_FIFA_World_Cup'
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    results = []
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # In Wikipedia, football matches are often in tables with class 'footballbox'
        matches = soup.find_all('div', class_='footballbox')
        
        match_id = 0
        for match in matches:
            try:
                teamA = match.find('th', class_='fhome').get_text(strip=True)
                teamB = match.find('th', class_='faway').get_text(strip=True)
                score_text = match.find('th', class_='fscore').get_text(strip=True)
                
                # Check if score is available (e.g. "2–1")
                # Sometimes it says "Match 1" if not played yet.
                scoreA = None
                scoreB = None
                
                if '–' in score_text: # en dash used in wiki
                    parts = score_text.split('–')
                    if len(parts) == 2 and parts[0].strip().isdigit() and parts[1].strip().isdigit():
                        scoreA = int(parts[0].strip())
                        scoreB = int(parts[1].strip())
                elif '-' in score_text:
                    parts = score_text.split('-')
                    if len(parts) == 2 and parts[0].strip().isdigit() and parts[1].strip().isdigit():
                        scoreA = int(parts[0].strip())
                        scoreB = int(parts[1].strip())
                        
                results.append({
                    'match_id': match_id,
                    'teamA': teamA,
                    'teamB': teamB,
                    'scoreA': scoreA,
                    'scoreB': scoreB,
                    'played': scoreA is not None and scoreB is not None
                })
                match_id += 1
            except Exception as e:
                continue
                
    except Exception as e:
        print("Error scraping Wikipedia:", e)

    # Map against predictions.json
    try:
        with open('predictions.json', 'r') as f:
            preds = json.load(f)
            
        def normalize_name(name):
            name = name.lower()
            name = name.replace('republic', '')
            name = name.replace('czechia', 'czech')
            name = name.replace('united states', 'usa')
            name = name.replace('bosnia and herzegovina', 'bosnia')
            name = name.replace('turkey', 'türkiye')
            return name.strip()
            
        pred_dict = {
            tuple(sorted([normalize_name(p['teamA']), normalize_name(p['teamB'])])): p['match_id']
            for p in preds
        }
        
        mapped_results = []
        for r in results:
            key = tuple(sorted([normalize_name(r['teamA']), normalize_name(r['teamB'])]))
            if key in pred_dict:
                r['match_id'] = pred_dict[key]
                mapped_results.append(r)
                
        results = mapped_results
    except Exception as e:
        print("Could not map to predictions.json:", e)

    # Save to real_results.json
    with open('real_results.json', 'w') as f:
        json.dump(results, f, indent=2)
        
    print(f"Scraped and mapped {len(results)} matches from Wikipedia.")

if __name__ == '__main__':
    scrape_world_cup_results()
