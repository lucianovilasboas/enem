#!/usr/bin/env python3
"""Extract campus lists from Wikipedia - hybrid approach (text + links)."""

import requests
import re
import csv
import time
from bs4 import BeautifulSoup

HEADERS = {'User-Agent': 'WikipediaCampusExtractor/3.0 (educational project)'}
API_URL = "https://pt.wikipedia.org/w/api.php"

def api_call(params, max_retries=5):
    params["format"] = "json"
    for attempt in range(max_retries):
        try:
            resp = requests.get(API_URL, params=params, headers=HEADERS, timeout=30)
            if resp.status_code == 200 and len(resp.text) > 10:
                return resp.json()
            if resp.status_code == 429:
                time.sleep(15)
        except:
            time.sleep(10)
    return None

SIGLA_MAP = {
    "Instituto Federal do Acre": "IFAC",
    "Instituto Federal de Alagoas": "IFAL",
    "Instituto Federal do Amapá": "IFAP",
    "Instituto Federal do Amazonas": "IFAM",
    "Instituto Federal da Bahia": "IFBA",
    "Instituto Federal Baiano": "IF Baiano",
    "Instituto Federal de Brasília": "IFB",
    "Instituto Federal Catarinense": "IFC",
    "Instituto Federal do Ceará": "IFCE",
    "Instituto Federal de Educação, Ciência e Tecnologia do Ceará": "IFCE",
    "Instituto Federal do Espírito Santo": "IFES",
    "Instituto Federal Farroupilha": "IF Farroupilha",
    "Instituto Federal Fluminense": "IFF",
    "Instituto Federal de Goiás": "IFG",
    "Instituto Federal Goiano": "IF Goiano",
    "Instituto Federal do Maranhão": "IFMA",
    "Instituto Federal de Mato Grosso": "IFMT",
    "Instituto Federal de Mato Grosso do Sul": "IFMS",
    "Instituto Federal de Minas Gerais": "IFMG",
    "Instituto Federal do Norte de Minas Gerais": "IFNMG",
    "Instituto Federal do Triângulo Mineiro": "IFTM",
    "Instituto Federal do Sudeste de Minas Gerais": "IF Sudeste MG",
    "Instituto Federal do Sul de Minas Gerais": "IF Sul de Minas",
    "Instituto Federal do Pará": "IFPA",
    "Instituto Federal da Paraíba": "IFPB",
    "Instituto Federal do Paraná": "IFPR",
    "Instituto Federal de Pernambuco": "IFPE",
    "Instituto Federal do Sertão Pernambucano": "IF Sertão PE",
    "Instituto Federal do Piauí": "IFPI",
    "Instituto Federal do Rio de Janeiro": "IFRJ",
    "Instituto Federal do Rio Grande do Norte": "IFRN",
    "Instituto Federal do Rio Grande do Sul": "IFRS",
    "Instituto Federal de Rondônia": "IFRO",
    "Instituto Federal de Roraima": "IFRR",
    "Instituto Federal de Santa Catarina": "IFSC",
    "Instituto Federal de São Paulo": "IFSP",
    "Instituto Federal de Sergipe": "IFS",
    "Instituto Federal Sul-rio-grandense": "IFSul",
    "Instituto Federal do Tocantins": "IFTO",
}

UF_MAP = {
    "Acre": "AC", "Alagoas": "AL", "Amapá": "AP", "Amazonas": "AM",
    "Bahia": "BA", "Baiano": "BA",
    "Brasília": "DF", "Catarinense": "SC", "Ceará": "CE",
    "Espírito Santo": "ES", "Farroupilha": "RS", "Fluminense": "RJ",
    "Goiás": "GO", "Goiano": "GO",
    "Maranhão": "MA", "Mato Grosso": "MT", "Mato Grosso do Sul": "MS",
    "Minas Gerais": "MG", "Norte de Minas Gerais": "MG",
    "Triângulo Mineiro": "MG", "Sudeste de Minas Gerais": "MG",
    "Sul de Minas Gerais": "MG",
    "Pará": "PA", "Paraíba": "PB", "Paraná": "PR",
    "Pernambuco": "PE", "Sertão Pernambucano": "PE",
    "Piauí": "PI", "Rio de Janeiro": "RJ",
    "Rio Grande do Norte": "RN", "Rio Grande do Sul": "RS",
    "Rondônia": "RO", "Roraima": "RR",
    "Santa Catarina": "SC", "São Paulo": "SP",
    "Sergipe": "SE", "Sul-rio-grandense": "RS",
    "Tocantins": "TO",
}

def get_uf(page_title):
    for prefix in ["do ", "de ", "da ", ""]:
        key = page_title.replace(f"Instituto Federal {prefix}", "")
        if key in UF_MAP:
            return UF_MAP[key]
    return ""

def get_actual_page(page_title):
    """Try to resolve the actual Wikipedia page."""
    params = {"action": "parse", "page": page_title, "prop": "text", "section": 0}
    data = api_call(params)
    if data and "parse" in data:
        return page_title
    
    # Try with redirects
    params["redirects"] = "1"
    data = api_call(params)
    if data and "parse" in data:
        actual = data["parse"].get("title", page_title)
        print(f"  (redirected to: {actual})", end=" ", flush=True)
        return actual
    
    # Try search  
    params2 = {"action": "query", "list": "search", "srsearch": page_title, "srlimit": 3}
    data = api_call(params2)
    if data and data.get("query", {}).get("search"):
        title = data["query"]["search"][0]["title"]
        if "Instituto Federal" in title:
            print(f"  (found via search: {title})", end=" ", flush=True)
            return title
    return None

def extract_campi(page_title):
    """Extract campus/city names from infobox."""
    time.sleep(0.7)
    
    actual = get_actual_page(page_title)
    if not actual:
        return None, "PAGE_NOT_FOUND"
    
    params = {"action": "parse", "page": actual, "prop": "text", "section": 0}
    data = api_call(params)
    if not data:
        return None, "API_FAIL"
    
    text = data["parse"]["text"]["*"]
    soup = BeautifulSoup(text, "html.parser")
    
    infobox = soup.find("table", class_="infobox")
    if not infobox:
        # Try alternative infobox class
        infobox = soup.find("table", class_="infobox_v2")
    if not infobox:
        return None, "NO_INFOBOX"
    
    # Extract data from infobox
    campi_text = None
    campi_links = None
    local_text = None
    local_links = None
    
    for row in infobox.find_all("tr"):
        th = row.find("th")
        if not th:
            continue
        label = th.get_text(strip=True)
        td = row.find("td")
        if not td:
            continue
        
        links = [a.get_text(strip=True) for a in td.find_all("a") 
                 if a.get_text(strip=True) and len(a.get_text(strip=True)) > 1
                 and not a.get("href", "").startswith("#")]
        
        if label in ["Campi", "Campus", "Unidades"]:
            campi_text = td.get_text(" ", strip=True)
            campi_links = links
        elif label == "Localização":
            local_text = td.get_text(" ", strip=True)
            local_links = links
    
    # Priority: If Campi has a real list (not just a number), use it
    if campi_text:
        # Check if it's just a number or "Lista"
        m = re.match(r'^(\d+)$', campi_text.strip())
        if m:
            pass  # Just a count number, don't use
        elif campi_text.strip().lower() == 'lista':
            pass  # "Lista" - need section extraction
        else:
            # Use comma-split from campi text
            if campi_links and len(campi_links) >= 3:
                return campi_links, "CAMPI_LINKS"
            elif ',' in campi_text:
                parts = re.split(r'\s*,\s*', campi_text)
                parts = [p.strip() for p in parts if p.strip() and len(p.strip()) > 2]
                parts = [p for p in parts if not re.match(r'^\d+$', p) and p.lower() not in ['lista']]
                if len(parts) >= 3:
                    return parts, "CAMPI_TEXT"
            else:
                # Remove leading number
                clean = re.sub(r'^\d+\s+(campi|campus|unidades|municípios)\s+', '', campi_text, flags=re.IGNORECASE)
                parts = re.split(r'\s{3,}', clean)
                parts = [p.strip() for p in parts if p.strip() and len(p.strip()) > 2]
                if len(parts) >= 3:
                    return parts, "CAMPI_TEXT"
    
    # Fallback: Localização text - remove state suffix and split
    if local_text:
        clean = local_text
        # Remove trailing state
        for state in list(UF_MAP.values()) + ["Brasil", "Brazil"]:
            clean = re.sub(rf',\s*{re.escape(state)}\s*$', '', clean, flags=re.IGNORECASE)
        
        # Use links if available (they preserve compound names)
        if local_links and len(local_links) >= 3:
            clean_links = [l for l in local_links if l not in UF_MAP.values() and l not in ["Brasil", "Brazil", "Localização", ""]]
            if len(clean_links) >= 3:
                return clean_links, "LOCAL_LINKS"
        
        # Comma split
        if ',' in clean:
            parts = [p.strip().rstrip(',;. ') for p in clean.split(',')]
            parts = [p for p in parts if p and len(p) > 2 and p.lower() not in ['sede', 'reitoria', 'localização', 'e']]
            if len(parts) >= 3:
                return parts, "LOCAL_TEXT"
        
        # Clean "e" connector: "X e Y" -> "X, Y"
        clean2 = re.sub(r'\s+e\s+', ', ', clean)
        if ',' in clean2:
            parts = [p.strip().rstrip(',;. ') for p in clean2.split(',')]
            parts = [p for p in parts if p and len(p) > 2 and p.lower() not in ['sede', 'reitoria', 'localização', 'e']]
            if len(parts) >= 2:
                return parts, "LOCAL_TEXT"
    
    return None, "NO_USABLE_DATA"

def main():
    # Get IF list 
    params = {
        "action": "parse",
        "page": "Instituto_Federal_de_Educação,_Ciência_e_Tecnologia",
        "prop": "text"
    }
    data = api_call(params)
    if not data:
        print("Failed to get IF list")
        return
    
    soup = BeautifulSoup(data["parse"]["text"]["*"], "html.parser")
    seen = set()
    if_pages = []
    for a in soup.find_all("a", href=True):
        title = a.get("title", "")
        if re.match(r'^/wiki/Instituto_Federal_', a["href"]) and title and title not in seen:
            if "Educação" not in title and "Ciência" not in title:
                seen.add(title)
                if_pages.append(title)
    
    # Add IFCE which uses a different page name
    if "Instituto Federal do Ceará" not in if_pages:
        if_pages.insert(0, "Instituto Federal de Educação, Ciência e Tecnologia do Ceará")
    
    # Deduplicate by sigla
    seen_siglas = set()
    unique_ifs = []
    for p in if_pages:
        sigla = SIGLA_MAP.get(p, "")
        if sigla and sigla not in seen_siglas:
            seen_siglas.add(sigla)
            unique_ifs.append(p)
    
    print(f"Found {len(unique_ifs)} unique IFs\n")
    
    all_results = []
    
    for i, page_title in enumerate(unique_ifs):
        sigla = SIGLA_MAP.get(page_title, "?")
        uf = get_uf(page_title)
        print(f"[{i+1}/{len(unique_ifs)}] {sigla:15s}...", end=" ", flush=True)
        
        cities, source = extract_campi(page_title)
        
        if cities is None:
            print(f"FAIL ({source})")
            continue
        
        # Clean and deduplicate
        seen_names = set()
        count = 0
        for c in cities:
            c = c.strip().rstrip(',;.()')
            c = re.sub(r'\s*\([^)]*\)\s*', '', c).strip()
            if c and c.lower() not in seen_names and len(c) > 2:
                noise = {'sede', 'reitoria', 'ead', 'localização', 'campus', 'campi'}
                if c.lower() not in noise and not re.match(r'^\d+$', c):
                    seen_names.add(c.lower())
                    all_results.append((c, uf, sigla))
                    count += 1
        
        print(f"{count} cities ({source})")
    
    # Deduplicate
    seen = set()
    unique_results = []
    for r in all_results:
        key = (r[0].lower(), r[1], r[2])
        if key not in seen:
            seen.add(key)
            unique_results.append(r)
    
    outpath = "dados/campi_wikipedia.csv"
    with open(outpath, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["municipio", "uf", "instituto_federal"])
        for r in sorted(unique_results, key=lambda x: (x[2], x[0])):
            w.writerow(r)
    
    print(f"\nTotal: {len(unique_results)} unique campuses saved to {outpath}\n")
    
    from collections import Counter
    cnt = Counter(r[2] for r in unique_results)
    for sigla, count in sorted(cnt.items(), key=lambda x: -x[1]):
        print(f"  {sigla:20s}: {count}")

if __name__ == "__main__":
    main()
