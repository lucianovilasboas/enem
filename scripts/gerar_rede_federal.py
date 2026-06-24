#!/usr/bin/env python3
"""Gera CSV unificado da Rede Federal de Educação, Ciência e Tecnologia.

Inclui:
  - Institutos Federais (IF) – base existente
  - CEFET-MG e CEFET-RJ
  - Colégio Pedro II (CPII)
  - UTFPR
  - Principais Escolas Técnicas Vinculadas (ETV)

Saída: dados/campi_rede_federal.csv
"""
import csv
import os
import time
import re
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

SAIDA = os.path.join("dados", "campi_rede_federal.csv")
EXISTENTE = os.path.join("dados", "campi_institutos_federais.csv")

# ─── Dados das instituições ───────────────────────────────────────

IFS_EXISTENTES = []  # será carregado do CSV existente

CEFETS = [
    ("CEFET-MG", "Minas Gerais", "Belo Horizonte", "MG"),
    ("CEFET-MG", "Minas Gerais", "Leopoldina", "MG"),
    ("CEFET-MG", "Minas Gerais", "Araxá", "MG"),
    ("CEFET-MG", "Minas Gerais", "Divinópolis", "MG"),
    ("CEFET-MG", "Minas Gerais", "Varginha", "MG"),
    ("CEFET-MG", "Minas Gerais", "Nepomuceno", "MG"),
    ("CEFET-MG", "Minas Gerais", "Timóteo", "MG"),
    ("CEFET-MG", "Minas Gerais", "Curvelo", "MG"),
    ("CEFET-RJ", "Rio de Janeiro", "Rio de Janeiro", "RJ"),
    ("CEFET-RJ", "Rio de Janeiro", "Angra dos Reis", "RJ"),
    ("CEFET-RJ", "Rio de Janeiro", "Itaguaí", "RJ"),
    ("CEFET-RJ", "Rio de Janeiro", "Valença", "RJ"),
    ("CEFET-RJ", "Rio de Janeiro", "Petrópolis", "RJ"),
    ("CEFET-RJ", "Rio de Janeiro", "Nova Friburgo", "RJ"),
]

# (instituicao, estado, municipio, municipio_merge, uf)
CPII = [
    ("Colégio Pedro II", "Rio de Janeiro", "Rio de Janeiro - Centro", "Rio de Janeiro", "RJ"),
    ("Colégio Pedro II", "Rio de Janeiro", "Rio de Janeiro - São Cristóvão", "Rio de Janeiro", "RJ"),
    ("Colégio Pedro II", "Rio de Janeiro", "Rio de Janeiro - Tijuca", "Rio de Janeiro", "RJ"),
    ("Colégio Pedro II", "Rio de Janeiro", "Rio de Janeiro - Realengo", "Rio de Janeiro", "RJ"),
    ("Colégio Pedro II", "Rio de Janeiro", "Rio de Janeiro - Engenho Novo", "Rio de Janeiro", "RJ"),
    ("Colégio Pedro II", "Rio de Janeiro", "Rio de Janeiro - Humaitá", "Rio de Janeiro", "RJ"),
    ("Colégio Pedro II", "Rio de Janeiro", "Duque de Caxias", "Duque de Caxias", "RJ"),
    ("Colégio Pedro II", "Rio de Janeiro", "Niterói", "Niterói", "RJ"),
]

UTFPR = [
    ("UTFPR", "Paraná", "Apucarana", "PR"),
    ("UTFPR", "Paraná", "Campo Mourão", "PR"),
    ("UTFPR", "Paraná", "Cornélio Procópio", "PR"),
    ("UTFPR", "Paraná", "Curitiba", "PR"),
    ("UTFPR", "Paraná", "Dois Vizinhos", "PR"),
    ("UTFPR", "Paraná", "Francisco Beltrão", "PR"),
    ("UTFPR", "Paraná", "Guarapuava", "PR"),
    ("UTFPR", "Paraná", "Londrina", "PR"),
    ("UTFPR", "Paraná", "Maringá", "PR"),
    ("UTFPR", "Paraná", "Pato Branco", "PR"),
    ("UTFPR", "Paraná", "Ponta Grossa", "PR"),
    ("UTFPR", "Paraná", "Santa Helena", "PR"),
    ("UTFPR", "Paraná", "Toledo", "PR"),
]

ETVS = [
    ("ETV", "COLTEC/UFMG", "Belo Horizonte", "MG"),
    ("ETV", "CT/UFRJ", "Rio de Janeiro", "RJ"),
    ("ETV", "CT/UFPE", "Recife", "PE"),
    ("ETV", "Colégio Técnico/UFU", "Uberlândia", "MG"),
    ("ETV", "Colégio Técnico/UFPR", "Curitiba", "PR"),
    ("ETV", "Escola Técnica/UFPA", "Belém", "PA"),
    ("ETV", "Colégio Técnico/UFRRJ", "Seropédica", "RJ"),
    ("ETV", "CAp/UFRRJ", "Seropédica", "RJ"),
    ("ETV", "Colégio Agrícola/UFES", "Alegre", "ES"),
    ("ETV", "Politécnico/UFSM", "Santa Maria", "RS"),
    ("ETV", "CTism/UFSM", "Santa Maria", "RS"),
    ("ETV", "Colégio Técnico/UFV", "Viçosa", "MG"),
    ("ETV", "Coltec/UFMG", "Belo Horizonte", "MG"),
    ("ETV", "Escola Técnica/UFU", "Uberlândia", "MG"),
    ("ETV", "Colégio Técnico/UNIFAL", "Alfenas", "MG"),
]


def carregar_ifs_existentes():
    """Carrega IFs do CSV existente (com coordenadas)."""
    registros = []
    with open(EXISTENTE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            registros.append({
                "sigla": row["instituto_federal"].strip(),
                "municipio": row["municipio"].strip(),
                "uf": row["uf"].strip().upper(),
                "latitude": row.get("latitude", "").strip(),
                "longitude": row.get("longitude", "").strip(),
            })
    return registros


def abrir_geocoder():
    geolocator = Nominatim(user_agent="enem-rede-federal-brasil/1.0")
    return RateLimiter(geolocator.geocode, min_delay_seconds=1.2)


def geocode(geocode_func, municipio, uf, sigla):
    """Tenta obter lat/lon para um campus."""
    queries = [
        f"{municipio}, {uf}, Brasil",
        f"{municipio} campus {sigla}, {uf}, Brasil",
        f"{municipio} {uf}, Brasil",
    ]
    for q in queries:
        try:
            location = geocode_func(q)
            if location:
                return location.latitude, location.longitude
        except Exception:
            time.sleep(2)
    return "", ""


def normalizar_municipio(nome):
    nome = nome.strip()
    nome = re.sub(r"\s*[-–—]\s*", " - ", nome)
    return nome


def main():
    os.makedirs("dados", exist_ok=True)
    print("Carregando IFs existentes...")
    ifs = carregar_ifs_existentes()
    print(f"  {len(ifs)} IFs carregados")

    # Organiza IFs existentes no formato unificado
    registros = []
    for r in ifs:
        registros.append({
            "municipio": r["municipio"],
            "municipio_merge": "",
            "uf": r["uf"],
            "instituicao": r["sigla"],
            "tipo_instituicao": "IF",
            "latitude": r["latitude"],
            "longitude": r["longitude"],
        })

    # Adiciona CEFETs
    for sigla, _, cidade, uf in CEFETS:
        registros.append({
            "municipio": cidade,
            "municipio_merge": "",
            "uf": uf,
            "instituicao": sigla,
            "tipo_instituicao": "CEFET",
            "latitude": "",
            "longitude": "",
        })

    # Adiciona CPII (usa municipio_merge para o match com ENEM)
    for _, _, campus, campus_merge, uf in CPII:
        registros.append({
            "municipio": campus,
            "municipio_merge": campus_merge,
            "uf": uf,
            "instituicao": "CPII",
            "tipo_instituicao": "CPII",
            "latitude": "",
            "longitude": "",
        })

    # Adiciona UTFPR
    for _, _, campus, uf in UTFPR:
        registros.append({
            "municipio": campus,
            "municipio_merge": "",
            "uf": uf,
            "instituicao": "UTFPR",
            "tipo_instituicao": "UTFPR",
            "latitude": "",
            "longitude": "",
        })

    # Adiciona ETVs
    for _, sigla, cidade, uf in ETVS:
        registros.append({
            "municipio": cidade,
            "municipio_merge": "",
            "uf": uf,
            "instituicao": sigla,
            "tipo_instituicao": "ETV",
            "latitude": "",
            "longitude": "",
        })

    # Geocoding para registros sem coordenadas
    pendentes = [r for r in registros if not r["latitude"] or not r["longitude"]]
    if pendentes:
        print(f"\n{len(pendentes)} campi sem coordenadas. Geocodificando...")
        geocode_func = abrir_geocoder()
        for i, r in enumerate(pendentes):
            lat, lon = geocode(geocode_func, r["municipio"], r["uf"], r["instituicao"])
            r["latitude"] = str(lat) if lat else ""
            r["longitude"] = str(lon) if lon else ""
            status = "OK" if lat else "FALHA"
            print(f"  [{i+1}/{len(pendentes)}] {r['instituicao']:20s} {r['municipio']:30s} {r['uf']} → {status}")
    else:
        print("Nenhum campus pendente de geocodificação.")

    # Deduplica
    vistos = set()
    unicos = []
    for r in registros:
        chave = (r["municipio"].lower(), r["uf"], r["instituicao"].upper())
        if chave not in vistos:
            vistos.add(chave)
            unicos.append(r)

    # Ordena
    ordem_tipo = {"IF": 0, "CEFET": 1, "CPII": 2, "UTFPR": 3, "ETV": 4}
    unicos.sort(key=lambda r: (ordem_tipo.get(r["tipo_instituicao"], 9), r["uf"], r["municipio"]))

    # Escreve CSV
    with open(SAIDA, "w", newline="", encoding="utf-8") as f:
        campos = ["municipio", "municipio_merge", "uf", "instituicao", "tipo_instituicao", "latitude", "longitude"]
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(unicos)

    print(f"\nCSV gerado: {SAIDA}")
    print(f"Total de registros: {len(unicos)}")
    from collections import Counter
    for tipo, qtde in sorted(Counter(r["tipo_instituicao"] for r in unicos).items()):
        com_coord = sum(1 for r in unicos if r["tipo_instituicao"] == tipo and r["latitude"])
        print(f"  {tipo:6s}: {qtde:3d} ({com_coord} com coordenadas)")


if __name__ == "__main__":
    main()
