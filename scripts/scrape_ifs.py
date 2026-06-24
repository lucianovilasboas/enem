#!/usr/bin/env python3
"""Scrape IF websites for campus listings and add new entries to CSV."""

import requests
import csv
import re
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin

HEADERS = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'}
TIMEOUT = 15

# IF list from ifs.html
IF_SITES = [
    ("IFAC", "AC", "https://portal.ifac.edu.br/"),
    ("IFAL", "AL", "https://www2.ifal.edu.br/"),
    ("IFAP", "AP", "https://ifap.edu.br/"),
    ("IFAM", "AM", "https://www2.ifam.edu.br/"),
    ("IFBA", "BA", "https://portal.ifba.edu.br/"),
    ("IF Baiano", "BA", "https://ifbaiano.edu.br/portal/"),
    ("IFB", "DF", "https://www.ifb.edu.br/"),
    ("IFCE", "CE", "https://ifce.edu.br/"),
    ("IFES", "ES", "https://www.ifes.edu.br/"),
    ("IFG", "GO", "https://www.ifg.edu.br/"),
    ("IF Goiano", "GO", "https://www.ifgoiano.edu.br/"),
    ("IFMA", "MA", "https://portal.ifma.edu.br/"),
    ("IFMG", "MG", "https://www.ifmg.edu.br/"),
    ("IFNMG", "MG", "https://www.ifnmg.edu.br/"),
    ("IF Sudeste MG", "MG", "https://www.ifsudestemg.edu.br/"),
    ("IF Sul de Minas", "MG", "https://portal.ifsuldeminas.edu.br/"),
    ("IFTM", "MG", "https://iftm.edu.br/"),
    ("IFMT", "MT", "https://ifmt.edu.br/"),
    ("IFMS", "MS", "https://www.ifms.edu.br/"),
    ("IFPA", "PA", "https://www.ifpa.edu.br/"),
    ("IFPB", "PB", "https://www.ifpb.edu.br/"),
    ("IFPE", "PE", "https://www.ifpe.edu.br/"),
    ("IF Sertão PE", "PE", "https://www.ifsertao-pe.edu.br/"),
    ("IFPI", "PI", "https://www.ifpi.edu.br/"),
    ("IFPR", "PR", "https://reitoria.ifpr.edu.br/"),
    ("IFRJ", "RJ", "https://portal.ifrj.edu.br/"),
    ("IFF", "RJ", "https://portal1.iff.edu.br/"),
    ("IFRN", "RN", "https://portal.ifrn.edu.br/"),
    ("IFRS", "RS", "https://ifrs.edu.br/"),
    ("IF Farroupilha", "RS", "https://www.iffarroupilha.edu.br/"),
    ("IFSul", "RS", "https://www.ifsul.edu.br/"),
    ("IFRO", "RO", "https://www.ifro.edu.br/"),
    ("IFRR", "RR", "https://www.ifrr.edu.br/"),
    ("IFSC", "SC", "https://www.ifsc.edu.br/"),
    ("IFC", "SC", "https://ifc.edu.br/"),
    ("IFSP", "SP", "https://www.ifsp.edu.br/"),
    ("IFS", "SE", "https://www.ifs.edu.br/"),
    ("IFTO", "TO", "https://www.ifto.edu.br/"),
]

def try_url_patterns(sigla, base_url):
    """Try common URL patterns to find campus listing pages."""
    patterns = [
        "campi",
        "campus",
        "unidades",
        "institucional/campi",
        "institucional/campus",
        "institucional/unidades",
        "institucional",
        "o-if/campi",
        "o-if/campus",
        "o-if/unidades",
        "a-instituicao/campi",
        "a-instituicao/campus",
        "a-instituicao/unidades",
        "ensino/campi",
        "ensino/campus",
        "campi-dos-if",
        "nossos-campi",
        "campi-if",
    ]
    
    for pattern in patterns:
        url = urljoin(base_url, pattern)
        try:
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            if resp.status_code == 200 and len(resp.text) > 500:
                cities = try_extract_cities(resp.text, sigla)
                if len(cities) >= 3:
                    return cities, pattern
        except:
            pass
    
    return [], None

def try_extract_cities(html, sigla):
    """Try to extract city names from HTML page."""
    soup = BeautifulSoup(html, "html.parser")
    
    # Remove non-content elements
    for tag in soup.find_all(['script', 'style', 'nav', 'footer', 'header']):
        tag.decompose()
    
    cities = []
    
    # Strategy 1: Look for links containing "campus" in text or href
    campus_links = []
    for a in soup.find_all('a', href=True):
        text = a.get_text(strip=True)
        href = a['href'].lower()
        if not text or len(text) < 3:
            continue
        # Only include links that look campus-related
        if any(kw in text.lower() for kw in ['campus', 'câmpus']) or 'campus' in href:
            # Extract city name from text after "Campus " or "Câmpus "
            city = re.sub(r'(?i)^(campus|câmpus)\s+', '', text).strip()
            if city and len(city) > 2:
                campus_links.append(city)
    
    if len(campus_links) >= 3:
        return campus_links
    
    # Strategy 2: Find all h2/h3 headings that contain "campus" or city names
    headings = []
    for h in soup.find_all(['h1', 'h2', 'h3', 'h4']):
        txt = h.get_text(strip=True)
        m = re.match(r'(?i)(?:campus|câmpus)\s+(.+?)(?:\s*[-–—]|\s*\([A-Z]{2,}\))?$', txt)
        if m:
            city = m.group(1).strip()
            if city and len(city) > 2:
                headings.append(city)
    
    if len(headings) >= 3:
        return headings
    
    # Strategy 3: Look for lists within campus sections
    # Find sections with "campi" or "campus" or "unidades" in heading
    for h in soup.find_all(['h1', 'h2', 'h3']):
        htxt = h.get_text(strip=True).lower()
        if any(kw in htxt for kw in ['campi', 'campus', 'câmpus', 'unidades']):
            # Get all links in subsequent content
            section = h.find_next(['div', 'ul', 'table'])
            if section:
                for a in section.find_all('a'):
                    txt = a.get_text(strip=True)
                    if txt and len(txt) > 3 and not any(kw in txt.lower() for kw in ['reitoria', 'ead', 'clique']):
                        cities.append(txt)
    
    if len(cities) >= 3:
        return cities
    
    # Strategy 4: Look for elements with class containing 'campus' 
    for el in soup.find_all(class_=lambda c: c and 'campus' in c.lower()):
        txt = el.get_text(strip=True)
        if txt and len(txt) > 2:
            cities.append(txt)
    
    return list(set(cities)) if len(cities) >= 3 else []

def main():
    # Read existing CSV
    existing = set()
    with open("dados/campi_institutos_federais.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing.add((row["municipio"].strip().lower(), row["uf"].strip(), row["instituto_federal"].strip()))
    
    all_new = []
    
    for sigla, uf, base_url in IF_SITES:
        print(f"\n[{sigla}] {base_url}")
        
        cities, pattern = try_url_patterns(sigla, base_url)
        
        if not cities:
            print(f"  No campus list found")
            continue
        
        new_for_if = []
        for city in cities:
            city = re.sub(r'(?i)^(campus|câmpus)\s+', '', city).strip()
            city = re.sub(r'\s*[-–—].*$', '', city).strip()
            city = re.sub(r'\s*\([^)]*\)\s*', '', city).strip()
            
            if not city or len(city) < 3:
                continue
            if any(kw in city.lower() for kw in ['ead', 'reitoria', 'clique', 'voltar', 'home']):
                continue
            if re.match(r'^\d+$', city):
                continue
            
            key = (city.lower(), uf, sigla)
            if key not in existing:
                new_for_if.append((city, uf, sigla))
                existing.add(key)
        
        if new_for_if:
            print(f"  Found via '{pattern}': {len(cities)} entries, {len(new_for_if)} new")
            for c, u, s in new_for_if:
                print(f"    + {c}/{u}/{s}")
            all_new.extend(new_for_if)
        else:
            print(f"  Found {len(cities)} entries (all already in CSV)")
        
        time.sleep(1)
    
    # Append new entries to CSV
    if all_new:
        with open("dados/campi_institutos_federais.csv", "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for city, uf, sigla in sorted(all_new, key=lambda x: (x[2], x[0])):
                writer.writerow([city, uf, sigla])
        print(f"\n\nAdded {len(all_new)} new campuses to CSV!")
    else:
        print("\n\nNo new campuses found.")

if __name__ == "__main__":
    main()
