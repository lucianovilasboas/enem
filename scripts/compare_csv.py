#!/usr/bin/env python3
"""Compare Wikipedia-extracted campuses against existing CSV."""
import csv
import re
from collections import defaultdict

def read_csv(path):
    data = set()
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            mun = row["municipio"].strip()
            uf = row["uf"].strip()
            sigla = row["instituto_federal"].strip()
            data.add((mun, uf, sigla))
    return data

# Read both CSVs
existing = read_csv("dados/campi_institutos_federais.csv")
wikipedia = read_csv("dados/campi_wikipedia.csv")

print(f"Existing CSV:  {len(existing)} entries")
print(f"Wikipedia CSV: {len(wikipedia)} entries\n")

# Group by IF
def group_by_if(data):
    groups = defaultdict(set)
    for mun, uf, sigla in data:
        groups[sigla].add((mun, uf))
    return groups

existing_groups = group_by_if(existing)
wiki_groups = group_by_if(wikipedia)

# Find in Wikipedia but not in existing (potential additions)
in_wiki_not_existing = defaultdict(set)
for mun, uf, sigla in wikipedia:
    if (mun, uf, sigla) not in existing:
        in_wiki_not_existing[sigla].add((mun, uf))

# Find in existing but not in Wikipedia (might be wrong or missing from Wikipedia)
in_existing_not_wiki = defaultdict(set)
for mun, uf, sigla in existing:
    if (mun, uf, sigla) not in wikipedia:
        in_existing_not_wiki[sigla].add((mun, uf))

print("=== IN WIKIPEDIA BUT NOT IN EXISTING CSV (candidates to ADD) ===")
total_add = 0
for sigla in sorted(in_wiki_not_existing.keys()):
    add = in_wiki_not_existing[sigla]
    if add:
        total_add += len(add)
        print(f"\n  {sigla} ({len(add)}):")
        for mun, uf in sorted(add):
            print(f"    + {mun}/{uf}")

print(f"\nTotal candidates to add: {total_add}")

print("\n\n=== IN EXISTING CSV BUT NOT IN WIKIPEDIA (potential issues) ===")
total_missing = 0
for sigla in sorted(in_existing_not_wiki.keys()):
    missing = in_existing_not_wiki[sigla]
    if missing:
        total_missing += len(missing)
        print(f"\n  {sigla} ({len(missing)} missing from Wikipedia of {len(existing_groups.get(sigla,[]))} total):")
        for mun, uf in sorted(missing):
            print(f"    - {mun}/{uf}")

print(f"\nTotal entries in existing but not Wikipedia: {total_missing}")
