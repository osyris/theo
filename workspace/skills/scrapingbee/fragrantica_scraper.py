#!/usr/bin/env python3
"""
Fragrantica scraper — extracts perfume data using ScrapingBee.
Parses: notes pyramid, accords (with colors!), rating, gender, year, perfumer.
Works with fragrantica.ru and fragrantica.com.
"""

import sys
import os
import re
import json

sys.path.insert(0, os.path.dirname(__file__))
from scrape import scrape


def clean_note_list(text):
    """Split notes by comma, handling parentheses correctly."""
    # First replace " и " / " and " with comma (but not inside parentheses)
    # Approach: temporarily replace content in parens
    protected = {}
    counter = [0]
    def protect(m):
        key = f"__PAREN{counter[0]}__"
        counter[0] += 1
        protected[key] = m.group(0)
        return key
    text = re.sub(r'\([^)]*\)', protect, text)
    text = re.sub(r'\s+и\s+', ', ', text)
    text = re.sub(r'\s+and\s+', ', ', text)
    parts = [p.strip() for p in text.split(',') if p.strip()]
    # Restore parenthesized content
    result = []
    for p in parts:
        for key, val in protected.items():
            p = p.replace(key, val)
        result.append(p)
    return result


def parse_fragrantica(html):
    """Parse Fragrantica perfume page HTML and extract structured data."""
    data = {}
    
    # === NOTES from meta/description text (most reliable) ===
    meta_match = re.search(
        r'(?:Верхние ноты|Top notes)[:\s]*(.+?);\s*'
        r'(?:средние ноты|middle notes|heart notes)[:\s]*(.+?);\s*'
        r'(?:базовые ноты|base notes)[:\s]*(.+?)(?:\.|<|")',
        html, re.I
    )
    
    if meta_match:
        data['pyramid'] = {
            'top': clean_note_list(meta_match.group(1)),
            'mid': clean_note_list(meta_match.group(2)),
            'base': clean_note_list(meta_match.group(3)),
        }
    else:
        # Fallback: parse from pyramid-note-label spans
        sections = re.split(
            r'(?:верхние|начальные|top)\s*нот\w*\s*</span>|'
            r'(?:средние|middle|heart)\s*нот\w*\s*</span>|'
            r'(?:базовые|base)\s*нот\w*\s*</span>',
            html, flags=re.I
        )
        pyramid = {'top': [], 'mid': [], 'base': []}
        keys = ['top', 'mid', 'base']
        for i, section in enumerate(sections[1:4]):
            if i < len(keys):
                notes = re.findall(r'pyramid-note-label[^>]*>\s*([^<]+?)\s*</span>', section)
                pyramid[keys[i]] = [n.strip() for n in notes if n.strip()]
        data['pyramid'] = pyramid
    
    # === ACCORDS with colors ===
    accord_pattern = r'background:\s*rgb\((\d+),\s*(\d+),\s*(\d+)\)[^"]*width:\s*(\d+(?:\.\d+)?)%[^>]*><span[^>]*>([^<]+)'
    matches = re.findall(accord_pattern, html)
    
    accords = []
    seen = set()
    for r, g, b, w, name in matches:
        name = name.strip()
        if name.lower() not in seen and len(name) > 1 and len(name) < 35:
            seen.add(name.lower())
            hex_color = f"#{int(r):02x}{int(g):02x}{int(b):02x}"
            accords.append({'name': name, 'w': round(float(w)), 'color': hex_color})
    
    data['accords'] = accords[:10]
    
    # === RATING ===
    rating_match = re.search(r'itemprop="ratingValue"[^>]*>([0-9.]+)', html)
    if not rating_match:
        rating_match = re.search(r'"ratingValue"\s*[":]+\s*([0-9.]+)', html)
    votes_match = re.search(r'itemprop="ratingCount"\s*content="(\d+)"', html)
    if not votes_match:
        votes_match = re.search(r'"ratingCount"\s*[":]+\s*(\d+)', html)
    
    if rating_match:
        data['rating'] = float(rating_match.group(1))
    if votes_match:
        data['votes'] = int(votes_match.group(1))
    
    # === GENDER ===
    if re.search(r'для женщин и мужчин|for women and men', html, re.I):
        data['gender'] = 'Унисекс'
    elif re.search(r'для женщин(?!\s*и)|for women(?!\s*and)', html, re.I):
        data['gender'] = 'Ж'
    elif re.search(r'для мужчин(?!\s*и)|for men(?!\s*and)', html, re.I):
        data['gender'] = 'М'
    
    # === YEAR ===
    year = re.search(r'(?:выпущен в|запущен в|launched in)\s*(\d{4})', html, re.I)
    if year:
        data['year'] = int(year.group(1))
    
    # === PERFUMER ===
    perfumer = re.search(r'(?:Парфюмер|Perfumer|Nose)[:\s]*(?:</[^>]*>\s*)*(?:<[^>]*>\s*)*([A-ZА-ЯЁ][^<]{2,55})', html, re.I)
    if perfumer:
        name = perfumer.group(1).strip().rstrip('.')
        if len(name) > 2 and not re.match(r'^(div|span|class|style)', name, re.I):
            data['perfumer'] = name
    
    # === CONCENTRATION ===
    conc = re.search(r'(Eau de Parfum|Eau de Toilette|Extrait de Parfum|Parfum Cologne|Cologne)', html, re.I)
    if conc:
        data['concentration'] = conc.group(1)
    
    # === FRAGRANTICA ID ===
    fid = re.search(r'/perfume/[^/]+/[^/]+-(\d+)\.html', html)
    if fid:
        data['fragrantica_id'] = int(fid.group(1))
    
    return data


def scrape_fragrantica(url, save_html=True):
    """Scrape a Fragrantica URL and return parsed data."""
    print(f"Scraping: {url}", file=sys.stderr)
    html = scrape(url, render_js=True, wait_ms=5000)
    if not html:
        print("ERROR: Failed to fetch page", file=sys.stderr)
        return None
    
    if save_html:
        with open('/tmp/fragrantica_last.html', 'w') as f:
            f.write(html)
        print(f"HTML saved ({len(html)} bytes)", file=sys.stderr)
    
    return parse_fragrantica(html)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <fragrantica_url>")
        sys.exit(1)
    
    result = scrape_fragrantica(sys.argv[1])
    if result:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        sys.exit(1)
