import requests
from bs4 import BeautifulSoup
import re
import json

# List of URLs to scrape (unchanged)
urls = [
    'https://deadfrontier.fandom.com/wiki/Melee_Weapons',
    'https://deadfrontier.fandom.com/wiki/Pistols',
    'https://deadfrontier.fandom.com/wiki/Rifles',
    'https://deadfrontier.fandom.com/wiki/Chainsaws',
    'https://deadfrontier.fandom.com/wiki/Shotguns',
    'https://deadfrontier.fandom.com/wiki/Sub-Machine_Guns',
    'https://deadfrontier.fandom.com/wiki/Assault_Rifles',
    'https://deadfrontier.fandom.com/wiki/Heavy_Machine_Guns',
    'https://deadfrontier.fandom.com/wiki/Grenade_Launchers',
    'https://deadfrontier.fandom.com/wiki/Flamethrowers',
    'https://deadfrontier.fandom.com/wiki/HCIM_Weapons,_Armour_%26_Clothings'
]

# Patterns dictionary (updated to include Damage per Burst)
patterns = {
    'DPS': re.compile(
        r'(?:Avg\. Damage per Second|Average Damage per Second):\s*.*?<b>([\d.]+)(?:\s*\(([\d.]+)\))?\s*</b>.*?Theoretical: <b>([\d.]+)(?:\s*\(([\d.]+)\))?\s*</b>',
        re.DOTALL),
    'Damage per Hit': re.compile(
        r'(?:Damage per Hit|Damage per Shot|Damage per Burst|Explosion Damage):.*?<b>(.*?)(?:\s*\((.*?)\))?</b>',
        re.DOTALL),
    'HPS': re.compile(
        r'(?:Hit\(s\) per Second|Shot\(s\) per Second):.*?<b>([\d.]+)</b>.*?Theoretical: <b>([\d.]+)</b>',
        re.DOTALL),
    'Melee Range': re.compile(
        r'Melee Range:.*?<b>([\d.]+)m</b>.*?Cleave Width:.*?<b>([\d.]+)m</b>',
        re.DOTALL),
    'Magazine Size': re.compile(r'Magazine Size:.*?<b>(\d+)</b>', re.DOTALL),
    'Reload Time': re.compile(r'Reload Time:.*?<b>([\d.]+)s</b>', re.DOTALL),
    'Critical Chance': re.compile(r'Critical Chance:.*?<b>([\d.]+)%</b>', re.DOTALL),
    'Knockback': re.compile(r'Knockback:.*?<b>([\d.]+)%</b>', re.DOTALL),
    'Accuracy': re.compile(r'Accuracy:.*?<b>([\d.]+)%</b>', re.DOTALL)
}


# Clean weapon name (unchanged)
def clean_weapon_name(name):
    # Remove tags like (Craft), (Dusk), etc.
    name = re.sub(r'\((Craft|Dusk|Challenge|LE|Unique)\)[^\n]*', '', name, flags=re.IGNORECASE)
    # Remove special characters, spaces, and convert to lowercase
    name = re.sub(r'[^a-zA-Z0-9]', '', name).lower()
    return name.strip()


# Scrape data from a single URL (unchanged)
def scrape_weapon_data(url, category):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    weapons_data = {}

    rows = soup.find_all('tr')
    i = 0
    while i < len(rows):
        row = rows[i]
        name_tag = row.find('th', colspan="2")
        if name_tag:
            raw_name = name_tag.get_text(strip=True)
            weapon_name = clean_weapon_name(raw_name)

            i += 1
            if i < len(rows):
                td = rows[i].find('td', width="320")
                if td:
                    html = str(td)
                    stats = {}
                    for key, pattern in patterns.items():
                        match = pattern.search(html)
                        if match:
                            stats[key] = match.groups()
                    weapons_data[weapon_name] = {
                        'category': category,
                        'stats': stats
                    }
        i += 1
    return weapons_data


# Main scraping logic (unchanged)
all_weapons = {}
for url in urls:
    category = url.split('/')[-1].replace('_', ' ').replace(', Armour %26 Clothings', '')
    print(f"Scraping {category}...")
    weapons = scrape_weapon_data(url, category)
    all_weapons.update(weapons)

# Structure the data for JSON (unchanged)
json_data = {
    "weapons": []
}
for name, data in all_weapons.items():
    weapon_entry = {
        "name": name,
        "category": data['category'],
        "stats": {}
    }
    for stat_name, stat_values in data['stats'].items():
        if stat_name == 'DPS' and stat_values:
            weapon_entry['stats']['DPS'] = {
                "real": stat_values[0],
                "theoretical": stat_values[2],
                "critical": stat_values[1] if stat_values[1] else None,
                "theoretical_critical": stat_values[3] if stat_values[3] else None
            }
        elif stat_name == 'Damage per Hit' and stat_values:
            # Clean the total field by removing <br> tags
            total_cleaned = re.sub(r'<br\s*/?>', '', stat_values[0]).strip() if stat_values[0] else None
            weapon_entry['stats']['DPH'] = {
                "total": total_cleaned,
                "critical": stat_values[1].strip() if stat_values[1] else None
            }
        elif stat_name == 'HPS' and stat_values:
            weapon_entry['stats']['HPS'] = {
                "real": stat_values[0],
                "theoretical": stat_values[1]
            }
        elif stat_name == 'Melee Range' and stat_values:
            weapon_entry['stats']['Melee Range'] = {
                "range": stat_values[0],
                "cleave_width": stat_values[1]
            }
        elif stat_name in ['Magazine Size', 'Reload Time', 'Critical Chance', 'Knockback', 'Accuracy'] and stat_values:
            weapon_entry['stats'][stat_name] = stat_values[0]

    json_data['weapons'].append(weapon_entry)

# Save to JSON file (unchanged)
with open('dead_frontier_weapons.json', 'w', encoding='utf-8') as f:
    json.dump(json_data, f, indent=4, ensure_ascii=False)

print("Data scraped and saved to 'dead_frontier_weapons.json'.")

# Generate TamperMonkey script (unchanged)
tampermonkey_template = f"""// ==UserScript==
// @name         Dead Frontier Weapon Data
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  Provides weapon data for Dead Frontier Tooltip DPS Injector
// @author       ils94
// @match        https://fairview.deadfrontier.com/onlinezombiemmo/index.php?page=24
// @match        https://fairview.deadfrontier.com/onlinezombiemmo/index.php?page=25
// @match        https://fairview.deadfrontier.com/onlinezombiemmo/index.php?page=28*
// @match        https://fairview.deadfrontier.com/onlinezombiemmo/index.php?page=35
// @match        https://fairview.deadfrontier.com/onlinezombiemmo/index.php?page=50
// @match        https://fairview.deadfrontier.com/onlinezombiemmo/index.php?page=59
// @match        https://fairview.deadfrontier.com/onlinezombiemmo/index.php?page=82*
// @match        https://fairview.deadfrontier.com/onlinezombiemmo/index.php?page=84
// @match        https://fairview.deadfrontier.com/onlinezombiemmo/DF3D/DF3D_InventoryPage.php?page=31*
// @match        https://fairview.deadfrontier.com/onlinezombiemmo/index.php?page=32*
// @license      MIT
// @grant        none
// @run-at       document-start
// @downloadURL https://update.greasyfork.org/scripts/535178/Dead%20Frontier%20Weapon%20Data.user.js
// @updateURL https://update.greasyfork.org/scripts/535178/Dead%20Frontier%20Weapon%20Data.meta.js
// ==/UserScript==

(function() {{
    'use strict';

    window.weaponData = {json.dumps(json_data, indent=4, ensure_ascii=False)};
}})();
"""

# Save TamperMonkey script (unchanged)
with open('dead_frontier_weapons.user.js', 'w', encoding='utf-8') as f:
    f.write(tampermonkey_template)

print("TamperMonkey script generated and saved to 'dead_frontier_weapons.user.js'.")
