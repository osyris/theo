#!/usr/bin/env python3
"""
Fragrantica scraper — extracts perfume data using ScrapingBee.
Parses: notes pyramid, accords, rating, longevity, sillage, seasons, gender, year, perfumer.
"""

import sys
import os
import re
import json

# Add skill dir to path
sys.path.insert(0, os.path.dirname(__file__))
from scrape import scrape

def parse_fragrantica(html):
    """Parse Fragrantica perfume page HTML and extract structured data."""
    data = {}
    
    # === NOTES PYRAMID ===
    # Russian Fragrantica: "Начальные ноты" / "Средние ноты" / "Базовые ноты"
    # English: "Top Notes" / "Middle Notes" / "Base Notes"
    
    # Method 1: Find note links with names
    # Pattern: <span>NoteName</span> near pyramid section markers
    
    # Split by note sections
    top_section = re.search(r'(?:Начальн|Top\s*Note|верхни)[^<]*</.*?(?=(?:Средни|Middle|Heart|Базов|Base)\s*[Нн]от|$)', html, re.S | re.I)
    mid_section = re.search(r'(?:Средни|Middle|Heart\s*Note|сердечн)[^<]*</.*?(?=(?:Базов|Base)\s*[Нн]от|$)', html, re.S | re.I)
    base_section = re.search(r'(?:Базов|Base\s*Note|базисн)[^<]*</.*?$', html, re.S | re.I)
    
    def extract_notes(section_html):
        if not section_html:
            return []
        text = section_html.group(0)[:5000]
        # Find note names in links: <a href="/notes/...">NoteName</a>
        # or: alt="NoteName" in img tags
        notes = re.findall(r'href="/notes?/[^"]*"[^>]*>\s*([^<]+?)\s*</a>', text)
        if not notes:
            notes = re.findall(r'alt="([^"]+?)"\s*(?:loading|class)', text)
        # Clean up
        notes = [n.strip() for n in notes if len(n.strip()) > 1 and len(n.strip()) < 50]
        return notes
    
    data['pyramid'] = {
        'top': extract_notes(top_section),
        'mid': extract_notes(mid_section),
        'base': extract_notes(base_section),
    }
    
    # === ACCORDS ===
    # Pattern: accord bars with names and widths
    # <div class="accord-bar" style="width: 85%">AccordName</div>
    accords_raw = re.findall(r'(?:width[:\s]*(\d+)%[^>]*>[^<]*<[^>]*>([^<]+)|class="[^"]*cell[^"]*accord[^"]*"[^>]*style="[^"]*width:\s*(\d+(?:\.\d+)?)%[^"]*"[^>]*>\s*([^<]+))', html)
    
    # Alternative pattern for Fragrantica.ru
    if not accords_raw:
        # Find accord-bar divs
        accord_blocks = re.findall(r'style="width:\s*(\d+(?:\.\d+)?)%[^"]*"[^>]*class="[^"]*accord[^"]*"[^>]*>\s*<[^>]*>\s*([^<]+)', html)
        if not accord_blocks:
            accord_blocks = re.findall(r'class="[^"]*accord[^"]*"[^>]*style="[^"]*width:\s*(\d+(?:\.\d+)?)%[^"]*"[^>]*>([^<]+)', html)
        accords_raw = [(w, n.strip(), '', '') for w, n in accord_blocks]
    
    accords = []
    for match in accords_raw:
        w = match[0] or match[2]
        n = (match[1] or match[3]).strip()
        if w and n and len(n) < 40:
            accords.append({'name': n, 'w': int(float(w))})
    data['accords'] = accords
    
    # === RATING ===
    rating_match = re.search(r'(?:itemprop="ratingValue"[^>]*content="([0-9.]+)"|"ratingValue"\s*:\s*"?([0-9.]+))', html)
    votes_match = re.search(r'(?:itemprop="ratingCount"[^>]*content="(\d+)"|"ratingCount"\s*:\s*"?(\d+)|"reviewCount"\s*:\s*"?(\d+))', html)
    if rating_match:
        data['rating'] = float(rating_match.group(1) or rating_match.group(2))
    if votes_match:
        data['votes'] = int(votes_match.group(1) or votes_match.group(2) or votes_match.group(3))
    
    # === LONGEVITY & SILLAGE ===
    # Look for longevity/sillage indicators
    longevity = re.search(r'(?:Стойкость|Longevity)[^<]*?(\d+[\s-]*\d*\s*(?:ч|h|час))', html, re.I)
    sillage = re.search(r'(?:Шлейф|Sillage)[^<]*?(\w+)', html, re.I)
    if longevity:
        data['longevity'] = longevity.group(1)
    if sillage:
        data['sillage'] = sillage.group(1)
    
    # === GENDER ===
    gender = re.search(r'(?:для женщин и мужчин|for women and men|унисекс|unisex)', html, re.I)
    if gender:
        data['gender'] = 'Унисекс'
    elif re.search(r'(?:для женщин|for women)', html, re.I):
        data['gender'] = 'Ж'
    elif re.search(r'(?:для мужчин|for men)', html, re.I):
        data['gender'] = 'М'
    
    # === YEAR ===
    year = re.search(r'(?:выпущен в|launched in|год выпуска:?)\s*(\d{4})', html, re.I)
    if not year:
        year = re.search(r'"datePublished"\s*:\s*"(\d{4})', html)
    if year:
        data['year'] = int(year.group(1))
    
    # === PERFUMER ===
    perfumer = re.search(r'(?:Парфюмер|Perfumer|Nose)[:\s]*</[^>]*>\s*<[^>]*>\s*([^<]+)', html, re.I)
    if not perfumer:
        perfumer = re.search(r'(?:Парфюмер|Perfumer|Nose)[:\s]*([^<,\.]{3,50})', html, re.I)
    if perfumer:
        data['perfumer'] = perfumer.group(1).strip()
    
    # === CONCENTRATION ===
    conc = re.search(r'(Eau de Parfum|Eau de Toilette|Extrait|Parfum|EDP|EDT)', html, re.I)
    if conc:
        data['concentration'] = conc.group(1)
    
    return data


def scrape_fragrantica(url):
    """Scrape a Fragrantica URL and return parsed data."""
    print(f"Scraping: {url}", file=sys.stderr)
    html = scrape(url, render_js=True, wait_ms=5000)
    if not html:
        print("ERROR: Failed to fetch page", file=sys.stderr)
        return None
    
    # Save raw HTML for debugging
    debug_path = '/tmp/fragrantica_last.html'
    with open(debug_path, 'w') as f:
        f.write(html)
    print(f"Raw HTML saved to {debug_path} ({len(html)} bytes)", file=sys.stderr)
    
    data = parse_fragrantica(html)
    return data


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <fragrantica_url>")
        print(f"Example: {sys.argv[0]} https://www.fragrantica.ru/perfume/Parfums-de-Marly/Delina-43871.html")
        sys.exit(1)
    
    result = scrape_fragrantica(sys.argv[1])
    if result:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("Failed to scrape", file=sys.stderr)
        sys.exit(1)
