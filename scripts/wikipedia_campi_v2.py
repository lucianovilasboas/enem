#!/usr/bin/env python3
"""Extract IF campus lists from Wikipedia using the python-wikipedia library."""
import wikipedia
import re
import csv
import time

# Set language and user agent
wikipedia.set_lang("pt")
import requests
wikipedia.requests = requests

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

def get_uf(page_title):
    uf_map = {
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
    for prefix in ["do ", "de ", "da ", ""]:
        key = page_title.replace(f"Instituto Federal {prefix}", "")
        if key in uf_map:
            return uf_map[key]
    return ""

def extract_from_html(html, sigla):
    """Extract city names from Wikipedia HTML."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    
    infobox = soup.find("table", class_="infobox")
    if not infobox:
        return []
    
    candidates = []
    for row in infobox.find_all("tr"):
        th = row.find("th")
        if not th:
            continue
        label = th.get_text(strip=True)
        if label not in ["Campi", "Campus", "Unidades", "Localização"]:
            continue
        td = row.find("td")
        if not td:
            continue
        
        # Get ALL link texts (city names are usually links)
        links = [a.get_text(strip=True) for a in td.find_all("a") 
                 if a.get_text(strip=True) and len(a.get_text(strip=True)) > 2
                 and not a.get("href", "").startswith("#")]
        
        # Filter out state abbreviations and common words  
        states = {'AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS',
                  'MG','PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO'}
        clean_links = [l for l in links if l not in states and l not in ['Brasil']]
        
        if clean_links:
            candidates.extend(clean_links)
        else:
            # No links - get text and split by comma
            text = td.get_text(" ", strip=True)
            # Remove leading number and "campi" word
            text = re.sub(r'^\d+\s+(campi|campus|unidades|municípios)\s+', '', text, flags=re.IGNORECASE)
            # Split by comma
            parts = [p.strip().rstrip(',;.') for p in text.split(',')]
            parts = [p for p in parts if p and len(p) > 2]
            candidates.extend(parts)
    
    return candidates

IF_PAGES = [
    "Instituto Federal do Acre",
    "Instituto Federal de Alagoas",
    "Instituto Federal do Amapá",
    "Instituto Federal do Amazonas",
    "Instituto Federal da Bahia",
    "Instituto Federal Baiano",
    "Instituto Federal de Brasília",
    "Instituto Federal Catarinense",
    "Instituto Federal do Ceará",
    "Instituto Federal de Educação, Ciência e Tecnologia do Ceará",
    "Instituto Federal do Espírito Santo",
    "Instituto Federal Farroupilha",
    "Instituto Federal Fluminense",
    "Instituto Federal de Goiás",
    "Instituto Federal Goiano",
    "Instituto Federal do Maranhão",
    "Instituto Federal de Mato Grosso",
    "Instituto Federal de Mato Grosso do Sul",
    "Instituto Federal de Minas Gerais",
    "Instituto Federal do Norte de Minas Gerais",
    "Instituto Federal do Triângulo Mineiro",
    "Instituto Federal do Sudeste de Minas Gerais",
    "Instituto Federal do Sul de Minas Gerais",
    "Instituto Federal do Pará",
    "Instituto Federal da Paraíba",
    "Instituto Federal do Paraná",
    "Instituto Federal de Pernambuco",
    "Instituto Federal do Sertão Pernambucano",
    "Instituto Federal do Piauí",
    "Instituto Federal do Rio de Janeiro",
    "Instituto Federal do Rio Grande do Norte",
    "Instituto Federal do Rio Grande do Sul",
    "Instituto Federal de Rondônia",
    "Instituto Federal de Roraima",
    "Instituto Federal de Santa Catarina",
    "Instituto Federal de São Paulo",
    "Instituto Federal de Sergipe",
    "Instituto Federal Sul-rio-grandense",
    "Instituto Federal do Tocantins",
]

def main():
    results = []
    seen_siglas = set()
    
    for page_title in IF_PAGES:
        sigla = SIGLA_MAP.get(page_title, "?")
        if sigla in seen_siglas:
            continue
        seen_siglas.add(sigla)
        
        uf = get_uf(page_title)
        print(f"[{len(seen_siglas)}/38] {sigla:15s}...", end=" ", flush=True)
        
        try:
            wp = wikipedia.page(page_title, auto_suggest=False)
            html = wp.html()
            cities = extract_from_html(html, sigla)
            
            if cities:
                seen = set()
                count = 0
                for c in cities:
                    c = c.strip().rstrip(',;.()')
                    c = re.sub(r'\s*\([^)]*\)\s*', '', c).strip()
                    if c and c.lower() not in seen and len(c) > 2:
                        noise = {'sede', 'reitoria', 'ead', 'localização', 'campus', 'campi'}
                        if c.lower() not in noise and not re.match(r'^\d+$', c):
                            if not c.startswith('http'):
                                seen.add(c.lower())
                                results.append((c, uf, sigla))
                                count += 1
                print(f"{count} cities")
            else:
                print("no data")
        except Exception as e:
            print(f"error: {e}")
        
        time.sleep(1)
    
    # Deduplicate
    seen = set()
    uniq = []
    for r in results:
        key = (r[0].lower(), r[1], r[2])
        if key not in seen:
            seen.add(key)
            uniq.append(r)
    
    with open("dados/campi_wikipedia.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["municipio", "uf", "instituto_federal"])
        for r in sorted(uniq, key=lambda x: (x[2], x[0])):
            w.writerow(r)
    
    print(f"\nTotal: {len(uniq)}")
    from collections import Counter
    for sig, ct in sorted(Counter(r[2] for r in uniq).items(), key=lambda x: -x[1]):
        print(f"  {sig:20s}: {ct}")

if __name__ == "__main__":
    main()
