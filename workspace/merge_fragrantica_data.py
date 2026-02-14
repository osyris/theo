#!/usr/bin/env python3
"""
Merge all scraped Fragrantica data and update the perfume page HTML.
This script:
1. Loads scraped data from JSON files
2. Updates HTML file with pyramid, accords, rating, votes, year, perfumer, concentration, gender
3. Does NOT change: brand, name, desc, tags, source, price, img, fav
"""

import json
import re
import os
from typing import Dict, Any, List, Optional

def load_json_from_file(filepath: str) -> List[Dict]:
    """Load JSON data from file, handling mixed raw output."""
    print(f"Loading {filepath}...")
    
    if not os.path.exists(filepath):
        print(f"File {filepath} not found!")
        return []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read().strip()
    
    if not content:
        print(f"File {filepath} is empty!")
        return []
    
    # Handle different formats
    if filepath.endswith('fragrantica_batch1.json'):
        # This is object format: {"Brand — Name": {...}, ...}
        try:
            data = json.loads(content)
            result = []
            for key, value in data.items():
                brand, name = key.split(' — ', 1)
                value['brand'] = brand
                value['name'] = name
                result.append(value)
            print(f"Loaded {len(result)} perfumes from batch1")
            return result
        except Exception as e:
            print(f"Error parsing batch1: {e}")
            return []
    
    elif filepath.endswith(('batch2_new.json', 'batch3.json')):
        # These are array formats with batch_name or perfume_name
        try:
            data = json.loads(content)
            result = []
            for item in data:
                if 'batch_name' in item:
                    # Format: "Brand — Name"
                    parts = item['batch_name'].split(' — ', 1)
                    if len(parts) == 2:
                        item['brand'] = parts[0]
                        item['name'] = parts[1]
                    else:
                        item['brand'] = item['batch_name']
                        item['name'] = item['batch_name']
                elif 'perfume_name' in item:
                    # Format: "Brand — Name"
                    parts = item['perfume_name'].split(' — ', 1)
                    if len(parts) == 2:
                        item['brand'] = parts[0]
                        item['name'] = parts[1]
                    else:
                        item['brand'] = item['perfume_name']
                        item['name'] = item['perfume_name']
                result.append(item)
            print(f"Loaded {len(result)} perfumes from {os.path.basename(filepath)}")
            return result
        except Exception as e:
            print(f"Error parsing {filepath}: {e}")
            return []
    
    elif filepath.endswith('batch4.json'):
        # This has raw scraper output mixed in - extract JSON objects
        try:
            # Find all JSON objects in the mixed content
            json_objects = []
            # Split by "Scraping:" to get sections
            sections = content.split('Scraping:')
            
            for section in sections[1:]:  # Skip first empty section
                # Find the JSON part (starts with {)
                brace_start = section.find('{')
                if brace_start == -1:
                    continue
                
                # Find matching closing brace
                brace_count = 0
                json_start = brace_start
                json_end = -1
                
                for i, char in enumerate(section[json_start:], json_start):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_end = i + 1
                            break
                
                if json_end > json_start:
                    json_str = section[json_start:json_end]
                    try:
                        obj = json.loads(json_str)
                        json_objects.append(obj)
                    except json.JSONDecodeError as e:
                        print(f"Failed to parse JSON object: {e}")
                        print(f"JSON string: {json_str[:200]}...")
            
            # Remove duplicates by fragrantica_id
            seen_ids = set()
            unique_objects = []
            for obj in json_objects:
                fid = obj.get('fragrantica_id')
                if fid and fid not in seen_ids:
                    seen_ids.add(fid)
                    unique_objects.append(obj)
                elif not fid:
                    unique_objects.append(obj)
            
            # Extract brand/name from URLs or try to infer
            result = []
            for obj in unique_objects:
                # Try to get brand/name - this data seems to be missing from batch4
                # We'll need to match by fragrantica_id later
                result.append(obj)
            
            print(f"Loaded {len(result)} perfumes from batch4 (unique)")
            return result
            
        except Exception as e:
            print(f"Error parsing batch4: {e}")
            return []
    
    else:
        print(f"Unknown file format: {filepath}")
        return []

def clean_perfumer_field(perfumer: str) -> Optional[str]:
    """Clean up the perfumer field that often contains HTML fragments."""
    if not perfumer or perfumer.strip() == '':
        return None
    
    # Remove HTML fragments
    if 'class="tw-header-nav-link">Парфюмеры' in perfumer:
        return None
    if 'href=' in perfumer or '<' in perfumer:
        return None
    
    # Clean up common patterns
    perfumer = perfumer.replace('...\">', '').strip()
    if perfumer in ['—', '', 's/', 's/']:
        return None
    
    return perfumer if len(perfumer) > 2 else None

def normalize_name(name: str) -> str:
    """Normalize perfume name for matching."""
    return name.lower().strip().replace('  ', ' ')

def find_perfume_in_html(brand: str, name: str, html_content: str) -> Optional[int]:
    """Find perfume index in HTML by matching brand and name."""
    # Extract perfume data from HTML
    match = re.search(r'const perfumes = \[(.*?)\];', html_content, re.DOTALL)
    if not match:
        return None
    
    perfume_array = match.group(1)
    
    # Find individual perfume objects
    objects = []
    brace_count = 0
    current_obj = ""
    
    for char in perfume_array:
        current_obj += char
        if char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0:
                objects.append(current_obj.strip())
                current_obj = ""
    
    # Search for matching perfume
    target_brand = normalize_name(brand)
    target_name = normalize_name(name)
    
    for i, obj_str in enumerate(objects):
        # Extract brand and name
        brand_match = re.search(r'brand\s*:\s*["\']([^"\']+)["\']', obj_str)
        name_match = re.search(r'name\s*:\s*["\']([^"\']+)["\']', obj_str)
        
        if brand_match and name_match:
            obj_brand = normalize_name(brand_match.group(1))
            obj_name = normalize_name(name_match.group(1))
            
            if obj_brand == target_brand and obj_name == target_name:
                return i
    
    return None

def format_pyramid(pyramid: Dict) -> str:
    """Format pyramid data for JavaScript."""
    top = ', '.join(pyramid.get('top', [])) if pyramid.get('top') else ''
    mid = ', '.join(pyramid.get('mid', [])) if pyramid.get('mid') else ''
    base = ', '.join(pyramid.get('base', [])) if pyramid.get('base') else ''
    
    return f'{{top:"{top}",mid:"{mid}",base:"{base}"}}'

def format_accords(accords: List[Dict]) -> str:
    """Format accords data for JavaScript."""
    if not accords:
        return '[]'
    
    accord_strs = []
    for accord in accords:
        name = accord.get('name', '').replace('"', '\\"')
        w = accord.get('w', 0)
        color = accord.get('color', '#cccccc')
        accord_strs.append(f'{{name:"{name}",w:{w},color:"{color}"}}')
    
    return f"[{','.join(accord_strs)}]"

def update_perfume_in_html(html_content: str, perfume_index: int, scraped_data: Dict) -> str:
    """Update a specific perfume in the HTML with scraped data."""
    # Extract perfume array from HTML
    match = re.search(r'(const perfumes = \[)(.*?)(\];)', html_content, re.DOTALL)
    if not match:
        return html_content
    
    prefix = match.group(1)
    perfume_array = match.group(2)
    suffix = match.group(3)
    
    # Find individual perfume objects
    objects = []
    brace_count = 0
    current_obj = ""
    
    for char in perfume_array:
        current_obj += char
        if char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0:
                objects.append(current_obj.strip())
                current_obj = ""
    
    if perfume_index >= len(objects):
        print(f"Error: perfume index {perfume_index} out of range")
        return html_content
    
    # Update the specific perfume object
    obj_str = objects[perfume_index]
    
    # Update pyramid
    if scraped_data.get('pyramid'):
        pyramid_str = format_pyramid(scraped_data['pyramid'])
        if 'pyramid:' in obj_str:
            obj_str = re.sub(r'pyramid\s*:\s*\{[^}]*\}', f'pyramid:{pyramid_str}', obj_str)
        else:
            # Add pyramid before the closing brace
            obj_str = obj_str.rstrip(' },') + f',\n    pyramid:{pyramid_str}' + obj_str[obj_str.rfind(' }'):] if obj_str.endswith(' }') else obj_str + f',pyramid:{pyramid_str}'
    
    # Update accords
    if scraped_data.get('accords'):
        accords_str = format_accords(scraped_data['accords'])
        if 'accords:' in obj_str:
            obj_str = re.sub(r'accords\s*:\s*\[[^\]]*\]', f'accords:{accords_str}', obj_str)
        else:
            obj_str = obj_str.rstrip(' },') + f',\n    accords:{accords_str}' + obj_str[obj_str.rfind(' }'):] if obj_str.endswith(' }') else obj_str + f',accords:{accords_str}'
    
    # Update rating
    if scraped_data.get('rating'):
        rating = scraped_data['rating']
        if 'rating:' in obj_str:
            obj_str = re.sub(r'rating\s*:\s*[^,}\s]+', f'rating:{rating}', obj_str)
        else:
            obj_str = obj_str.rstrip(' },') + f',\n    rating:{rating}' + (obj_str[obj_str.rfind(' }'):] if obj_str.endswith(' }') else '')
    
    # Update votes
    if scraped_data.get('votes'):
        votes = scraped_data['votes']
        if 'votes:' in obj_str:
            obj_str = re.sub(r'votes\s*:\s*[^,}\s]+', f'votes:{votes}', obj_str)
        else:
            obj_str = obj_str.rstrip(' },') + f',\n    votes:{votes}' + (obj_str[obj_str.rfind(' }'):] if obj_str.endswith(' }') else '')
    
    # Update year
    if scraped_data.get('year'):
        year = scraped_data['year']
        if 'year:' in obj_str:
            obj_str = re.sub(r'year\s*:\s*[^,}\s]+', f'year:{year}', obj_str)
        else:
            obj_str = obj_str.rstrip(' },') + f',\n    year:{year}' + (obj_str[obj_str.rfind(' }'):] if obj_str.endswith(' }') else '')
    
    # Update perfumer
    perfumer = clean_perfumer_field(scraped_data.get('perfumer', ''))
    if perfumer:
        if 'perfumer:' in obj_str:
            obj_str = re.sub(r'perfumer\s*:\s*["\'][^"\']*["\']', f'perfumer:"{perfumer}"', obj_str)
        else:
            obj_str = obj_str.rstrip(' },') + f',\n    perfumer:"{perfumer}"' + (obj_str[obj_str.rfind(' }'):] if obj_str.endswith(' }') else '')
    
    # Update concentration
    if scraped_data.get('concentration'):
        conc = scraped_data['concentration'].replace('"', '\\"')
        if 'concentration:' in obj_str:
            obj_str = re.sub(r'concentration\s*:\s*["\'][^"\']*["\']', f'concentration:"{conc}"', obj_str)
        else:
            obj_str = obj_str.rstrip(' },') + f',\n    concentration:"{conc}"' + (obj_str[obj_str.rfind(' }'):] if obj_str.endswith(' }') else '')
    
    # Update gender
    if scraped_data.get('gender'):
        gender = scraped_data['gender'].replace('"', '\\"')
        if 'gender:' in obj_str:
            obj_str = re.sub(r'gender\s*:\s*["\'][^"\']*["\']', f'gender:"{gender}"', obj_str)
        else:
            obj_str = obj_str.rstrip(' },') + f',\n    gender:"{gender}"' + (obj_str[obj_str.rfind(' }'):] if obj_str.endswith(' }') else '')
    
    # Update the object in the array
    objects[perfume_index] = obj_str
    
    # Reconstruct HTML
    new_perfume_array = ',\n\n  '.join(objects)
    new_html = html_content.replace(match.group(0), f'{prefix}\n  {new_perfume_array}\n{suffix}')
    
    return new_html

def main():
    """Main function to merge all Fragrantica data."""
    print("🔄 Starting Fragrantica data merge...")
    
    # File paths
    batch_files = [
        '/tmp/fragrantica_batch1.json',
        '/tmp/fragrantica_batch2_new.json', 
        '/tmp/fragrantica_batch3.json',
        '/tmp/fragrantica_batch4.json'
    ]
    
    html_file = '/data/workspace/pages/perfume/index.html'
    
    # Load all scraped data
    all_perfumes = []
    for filepath in batch_files:
        batch_data = load_json_from_file(filepath)
        all_perfumes.extend(batch_data)
    
    # Add Delina data (manually parsed from HTML)
    delina_data = {
        'brand': 'Parfums de Marly',
        'name': 'Delina',
        'rating': 3.98,
        'votes': 12572
    }
    all_perfumes.append(delina_data)
    
    print(f"\n📊 Total perfumes loaded: {len(all_perfumes)}")
    
    # Load HTML file
    if not os.path.exists(html_file):
        print(f"❌ HTML file not found: {html_file}")
        return
    
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Update perfumes in HTML
    updated_count = 0
    
    for perfume in all_perfumes:
        brand = perfume.get('brand')
        name = perfume.get('name') 
        
        if not brand or not name:
            # Try to extract from batch_name or perfume_name
            if 'batch_name' in perfume:
                parts = perfume['batch_name'].split(' — ', 1)
                brand, name = parts if len(parts) == 2 else (perfume['batch_name'], '')
            elif 'perfume_name' in perfume:
                parts = perfume['perfume_name'].split(' — ', 1)
                brand, name = parts if len(parts) == 2 else (perfume['perfume_name'], '')
            else:
                print(f"⚠️  Skipping perfume with missing brand/name: {perfume}")
                continue
        
        # Find perfume in HTML
        perfume_index = find_perfume_in_html(brand, name, html_content)
        
        if perfume_index is not None:
            print(f"✅ Updating: {brand} — {name}")
            html_content = update_perfume_in_html(html_content, perfume_index, perfume)
            updated_count += 1
        else:
            print(f"❌ Not found in HTML: {brand} — {name}")
    
    # Write updated HTML back to file
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n🎉 Update complete!")
    print(f"   📄 Updated {updated_count} perfumes")
    print(f"   📊 Total perfumes processed: {len(all_perfumes)}")
    print(f"   💾 HTML file updated: {html_file}")

if __name__ == '__main__':
    main()