#!/usr/bin/env python3
"""Universal web scraper using ScrapingBee API."""

import sys
import os
import urllib.parse
import subprocess
import json

def get_api_key():
    """Load API key from .env file."""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith('SCRAPINGBEE_API_KEY='):
                    return line.strip().split('=', 1)[1]
    key = os.environ.get('SCRAPINGBEE_API_KEY')
    if key:
        return key
    print("ERROR: No API key found. Set SCRAPINGBEE_API_KEY in .env or environment.", file=sys.stderr)
    sys.exit(1)

def scrape(url, render_js=True, wait_ms=3000, premium_proxy=False):
    """Scrape a URL using ScrapingBee API. Returns HTML string."""
    api_key = get_api_key()
    encoded_url = urllib.parse.quote(url, safe='')
    
    api_url = f"https://app.scrapingbee.com/api/v1?api_key={api_key}&url={encoded_url}"
    if render_js:
        api_url += "&render_js=true"
    if wait_ms:
        api_url += f"&wait={wait_ms}"
    if premium_proxy:
        api_url += "&premium_proxy=true"
    
    result = subprocess.run(
        ['curl', '-s', '-w', '\n%{http_code}', api_url],
        capture_output=True, text=True, timeout=60
    )
    
    output = result.stdout
    lines = output.rsplit('\n', 1)
    html = lines[0] if len(lines) > 1 else output
    status = lines[1] if len(lines) > 1 else '000'
    
    if status != '200':
        print(f"ERROR: HTTP {status}", file=sys.stderr)
        if len(html) < 500:
            print(html, file=sys.stderr)
        return None
    
    return html

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <url> [--no-js] [--wait MS] [--premium]")
        sys.exit(1)
    
    url = sys.argv[1]
    render_js = '--no-js' not in sys.argv
    wait_ms = 3000
    premium = '--premium' in sys.argv
    
    for i, arg in enumerate(sys.argv):
        if arg == '--wait' and i + 1 < len(sys.argv):
            wait_ms = int(sys.argv[i + 1])
    
    html = scrape(url, render_js=render_js, wait_ms=wait_ms, premium_proxy=premium)
    if html:
        print(html)
