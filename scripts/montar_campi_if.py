import requests
from bs4 import BeautifulSoup
import re
import csv
import os
import time

UFS = [
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA",
    "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN",
    "RS", "RO", "RR", "SC", "SP", "SE", "TO",
]

# Padrão para detectar linha com cidade, UF e CEP
RE_CIDADE_UF = re.compile(r"([^,]+),\s*([A-Z]{2})\.\s*CEP:")
RE_CIDADE_UF_SIMPLES = re.compile(r"([^,]+),\s*([A-Z]{2})\.")

# Nomes de IFs (nomes oficiais abreviados para o CSV)
def sigla_if(nome_completo):
    nome = nome_completo.upper().strip()
    nome_norm = nome.replace("DE EDUCACAO, CIENCIA E TECNOLOGIA", "").replace("DE EDUCAÇÃO, CIÊNCIA E TECNOLOGIA", "").replace("INSTITUTO FEDERAL", "").strip()

    # Padrões específicos (devem vir antes dos genéricos)
    matches = [
        ("ACRE", "IFAC"), ("IFAC", "IFAC"),
        ("ALAGOAS", "IFAL"), ("IFAL", "IFAL"),
        ("AMAPÁ", "IFAP"), ("AMAPA", "IFAP"), ("IFAP", "IFAP"),
        ("AMAZONAS", "IFAM"), ("IFAM", "IFAM"),
        ("BAIANO", "IF Baiano"),
        ("BAHIA", "IFBA"), ("IFBA", "IFBA"),
        ("CEARÁ", "IFCE"), ("CEARA", "IFCE"), ("IFCE", "IFCE"),
        ("BRASÍLIA", "IFB"), ("BRASILIA", "IFB"), ("IFB", "IFB"),
        ("ESPÍRITO SANTO", "IFES"), ("ESPIRITO SANTO", "IFES"), ("IFES", "IFES"),
        ("GOIÁS", "IFG"), ("GOIAS", "IFG"), ("IFG", "IFG"),
        ("GOIANO", "IF Goiano"),
        ("MARANHÃO", "IFMA"), ("MARANHAO", "IFMA"), ("IFMA", "IFMA"),
        ("MATO GROSSO DO SUL", "IFMS"), ("IFMS", "IFMS"),
        ("MATO GROSSO", "IFMT"), ("IFMT", "IFMT"),
        ("IFMG", "IFMG"),
        ("MINAS GERAIS", None),  # precisa desambiguação
        ("NORTE DE MINAS", "IFNMG"), ("IFNMG", "IFNMG"),
        ("SUDESTE DE MINAS", "IF Sudeste MG"),
        ("SUL DE MINAS", "IF Sul de Minas"),
        ("TRIÂNGULO MINEIRO", "IFTM"), ("TRIANGULO MINEIRO", "IFTM"),

        ("PARÁ", "IFPA"), ("IFPA", "IFPA"),
        ("PARAÍBA", "IFPB"), ("PARAIBA", "IFPB"), ("IFPB", "IFPB"),
        ("PARANÁ", "IFPR"), ("PARANA", "IFPR"), ("IFPR", "IFPR"),
        ("SERTÃO", "IF Sertão PE"), ("SERTAO", "IF Sertão PE"),
        ("PERNAMBUCO", "IFPE"), ("IFPE", "IFPE"),
        ("PIAUÍ", "IFPI"), ("PIAUI", "IFPI"), ("IFPI", "IFPI"),
        ("FLUMINENSE", "IFF"), ("IFF", "IFF"),
        ("RIO DE JANEIRO", "IFRJ"), ("IFRJ", "IFRJ"),
        ("RIO GRANDE DO NORTE", "IFRN"), ("IFRN", "IFRN"),
        ("RIO GRANDE DO SUL", None),  # precisa desambiguação
        ("FARROUPILHA", "IF Farroupilha"),
        ("SUL-RIO-GRANDENSE", "IFSul"), ("SUL RIO GRANDENSE", "IFSul"),
        ("IFRS", "IFRS"),
        ("RONDÔNIA", "IFRO"), ("RONDONIA", "IFRO"), ("IFRO", "IFRO"),
        ("RORAIMA", "IFRR"), ("IFRR", "IFRR"),
        ("SANTA CATARINA", None),  # precisa desambiguação
        ("CATARINENSE", "IFC"), ("IFC", "IFC"),
        ("IFSC", "IFSC"),
        ("SÃO PAULO", "IFSP"), ("SAO PAULO", "IFSP"), ("IFSP", "IFSP"),
        ("SERGIPE", "IFS"), ("IFS", "IFS"),
        ("TOCANTINS", "IFTO"), ("IFTO", "IFTO"),
    ]

    # CEFET e CPII (precisam ser verificados antes das desambiguações)
    if "CEFET-MG" in nome or "CEFETMG" in nome:
        return "CEFET-MG"
    if "CEFET-RJ" in nome or "CEFETRJ" in nome or "CELSO SUCKOW" in nome:
        return "CEFET-RJ"
    if "COLÉGIO PEDRO" in nome or "COLEGIO PEDRO" in nome:
        return "CPII"

    # Desambiguação para RS
    if "RIO GRANDE DO SUL" in nome:
        if "FARROUPILHA" in nome:
            return "IF Farroupilha"
        if "SUL-RIO-GRANDENSE" in nome or "SUL RIO GRANDENSE" in nome:
            return "IFSul"
        return "IFRS"

    # Desambiguação para MG
    if "MINAS GERAIS" in nome:
        if "NORTE DE MINAS" in nome or "NORTE" in nome_norm:
            return "IFNMG"
        if "SUDESTE DE MINAS" in nome or "SUDESTE" in nome_norm:
            return "IF Sudeste MG"
        if "SUL DE MINAS" in nome or "SUL" in nome_norm:
            return "IF Sul de Minas"
        if "TRIÂNGULO MINEIRO" in nome or "TRIANGULO MINEIRO" in nome:
            return "IFTM"
        return "IFMG"

    # Desambiguação para SC
    if "SANTA CATARINA" in nome:
        if "CATARINENSE" in nome:
            return "IFC"
        return "IFSC"

    # Varredura de padrões
    for padrao, sigla in matches:
        if padrao in nome:
            if sigla is not None:
                return sigla

    return nome_completo.strip()[:40]


PREPOSICOES = {"Do", "Da", "De", "Das", "Dos", "E"}

def limpar_cidade(nome):
    nome = nome.strip()
    nome = re.sub(r"\s+", " ", nome)
    return nome

def proper_title(s):
    palavras = s.strip().split()
    resultado = []
    for i, p in enumerate(palavras):
        p = p.capitalize()
        if i > 0 and p in PREPOSICOES:
            p = p.lower()
        resultado.append(p)
    return " ".join(resultado)


def extrair_cidade_uf(texto):
    m = RE_CIDADE_UF.search(texto)
    if m:
        return limpar_cidade(m.group(1)), m.group(2)
    m = RE_CIDADE_UF_SIMPLES.search(texto)
    if m:
        return limpar_cidade(m.group(1)), m.group(2)
    return None, None


def parse_simec_uf(uf):
    url = f"https://simec.mec.gov.br/academico/mapa/dados_instituto_edpro.php?uf={uf}"
    try:
        r = requests.get(url, timeout=60)
        r.encoding = "ISO-8859-1"
    except Exception as e:
        print(f"  ERRO ao acessar {uf}: {e}")
        return []
    soup = BeautifulSoup(r.text, "html.parser")
    rows = []
    current_if = None
    for p in soup.find_all("p", class_="instituto_federal_titulo"):
        texto = p.get_text(strip=True)
        # É um cabeçalho de instituição?
        if texto.startswith("INSTITUTO FEDERAL") or texto.startswith("CEFET") or texto.startswith("COLÉGIO PEDRO"):
            current_if = texto
            continue
        # É um campus / unidade
        if texto.startswith("CAMPUS") or texto.startswith("UNED") or texto.startswith("UNIDADE") or texto.startswith("POLO"):
            campus_nome = texto
            if current_if is None:
                continue
            ul = p.find_next("ul")
            if ul:
                for li in ul.find_all("li"):
                    li_text = li.get_text(strip=True)
                    cidade, uf_encontrada = extrair_cidade_uf(li_text)
                    if cidade and uf_encontrada:
                        rows.append((cidade, uf_encontrada, current_if, campus_nome))
                        break
    return rows


def main():
    saida = os.path.join("dados", "campi_institutos_federais.csv")
    os.makedirs("dados", exist_ok=True)

    todas_linhas = []
    ufs_processadas = []

    print("=== Etapa 1: Scraping SIMEC/MEC por estado ===\n")
    for uf in UFS:
        print(f"  Processando {uf}...", end=" ", flush=True)
        linhas = parse_simec_uf(uf)
        print(f"{len(linhas)} campi encontrados")
        todas_linhas.extend(linhas)
        ufs_processadas.append(uf)
        time.sleep(0.5)

    print(f"\n  Total de registros SIMEC: {len(todas_linhas)}")

    print("\n=== Etapa 2: Adicionando novos campi (expansão 2024-2026) ===\n")

    # Novos campi autorizados em março/2026 (Portaria MEC nº 267/2026)
    # e anunciados em 2024 (100 novos campi do PAC)
    novos_campi = [
        # AC
        ("Tartarugalzinho", "AP", "IFAP"),
        # BA
        ("Remanso", "BA", "IF Baiano"),
        ("Ribeira do Pombal", "BA", "IF Baiano"),
        ("Ruy Barbosa", "BA", "IF Baiano"),
        ("Santo Estêvão", "BA", "IF Baiano"),
        ("Poções", "BA", "IFBA"),
        ("Itabuna", "BA", "IFBA"),
        ("Macaúbas", "BA", "IFBA"),
        ("Salvador", "BA", "IFBA"),
        # GO
        ("Quirinópolis", "GO", "IFG"),
        ("Porangatu", "GO", "IFG"),
        ("Cavalcante", "GO", "IFG"),
        # MA
        ("Colinas", "MA", "IFMA"),
        ("Chapadinha", "MA", "IFMA"),
        ("Balsas", "MA", "IFMA"),
        ("Amarante do Maranhão", "MA", "IFMA"),
        # MG
        ("Bom Despacho", "MG", "IFMG"),
        ("João Monlevade", "MG", "IFMG"),
        ("Minas Novas", "MG", "IFNMG"),
        ("Itajubá", "MG", "IF Sul de Minas"),
        ("Sete Lagoas", "MG", "IFTM"),
        ("Caratinga", "MG", "IFMG"),
        ("São João Nepomuceno", "MG", "IF Sudeste MG"),
        ("Belo Horizonte", "MG", "IFMG"),
        # MT
        ("Colniza", "MT", "IFMT"),
        ("Água Boa", "MT", "IFMT"),
        ("Canarana", "MT", "IFMT"),
        ("Campo Verde", "MT", "IFMT"),
        # PE
        ("Goiana", "PE", "IFPE"),
        ("Santa Cruz do Capibaribe", "PE", "IFPE"),
        ("Recife", "PE", "IFPE"),
        ("Araripina", "PE", "IF Sertão PE"),
        ("Águas Belas", "PE", "IFPE"),
        ("Bezerros", "PE", "IFPE"),
        # PI
        ("Altos", "PI", "IFPI"),
        ("Barras", "PI", "IFPI"),
        ("Esperantina", "PI", "IFPI"),
        # RJ
        ("Rio de Janeiro - Cidade de Deus", "RJ", "IFRJ"),
        ("Rio de Janeiro - Complexo do Alemão", "RJ", "IFRJ"),
        ("Magé", "RJ", "IFF"),
        ("Belford Roxo", "RJ", "IFRJ"),
        ("Teresópolis", "RJ", "IFRJ"),
        ("São Gonçalo", "RJ", "IFF"),
        # RN
        ("São Miguel", "RN", "IFRN"),
        ("Touros", "RN", "IFRN"),
        ("Umarizal", "RN", "IFRN"),
        # RS
        ("São Luiz Gonzaga", "RS", "IF Farroupilha"),
        ("Porto Alegre - Zona Norte", "RS", "IFRS"),
        ("São Leopoldo", "RS", "IFRS"),
        ("Gramado", "RS", "IFRS"),
        ("Caçapava do Sul", "RS", "IFSul"),
        ("Santiago", "RS", "IF Farroupilha"),
        # SP
        ("Cotia", "SP", "IFSP"),
        ("Diadema", "SP", "IFSP"),
        ("Guarujá", "SP", "IFSP"),
        ("Mauá", "SP", "IFSP"),
        ("Osasco", "SP", "IFSP"),
        ("Ribeirão Preto", "SP", "IFSP"),
        ("Santos", "SP", "IFSP"),
        ("São Paulo - Cidade Tiradentes", "SP", "IFSP"),
        ("São Paulo - Jardim Ângela", "SP", "IFSP"),
        ("São Vicente", "SP", "IFSP"),
        ("Sumaré", "SP", "IFSP"),
        ("Franco da Rocha", "SP", "IFSP"),
        ("Carapicuíba", "SP", "IFSP"),
        # TO
        ("Tocantinópolis", "TO", "IFTO"),
        # ES
        ("Muniz Freire", "ES", "IFES"),
        # PA
        ("Barcarena", "PA", "IFPA"),
        ("Redenção", "PA", "IFPA"),
        ("Tailândia", "PA", "IFPA"),
        ("Alenquer", "PA", "IFPA"),
        ("Viseu", "PA", "IFPA"),
        # AM
        ("Santo Antônio do Içá", "AM", "IFAM"),
        ("Manicoré", "AM", "IFAM"),
        # TO (Norte)
        ("Butiritis", "TO", "IFTO"),
        # AC
        ("Feijó", "AC", "IFAC"),
        # RR
        ("Rorainópolis", "RR", "IFRR"),
        # CE
        ("Cascavel", "CE", "IFCE"),
        ("Mauriti", "CE", "IFCE"),
        ("Campos Sales", "CE", "IFCE"),
        ("Lavras de Mangabeira", "CE", "IFCE"),
        ("Fortaleza", "CE", "IFCE"),
        # PB
        ("Mamanguape", "PB", "IFPB"),
        ("Sapé", "PB", "IFPB"),
        ("Queimadas", "PB", "IFPB"),
        # AL
        ("Girau do Ponciano", "AL", "IFAL"),
        ("Mata Grande", "AL", "IFAL"),
        ("Maceió", "AL", "IFAL"),
        # SE
        ("Japaratuba", "SE", "IFS"),
        ("Aracaju", "SE", "IFS"),
        # PR
        ("Maringá", "PR", "IFPR"),
        ("Araucária", "PR", "IFPR"),
        ("Cianorte", "PR", "IFPR"),
        ("Cambé", "PR", "IFPR"),
        ("Toledo", "PR", "IFPR"),
        # SC
        ("Tijucas", "SC", "IFC"),
        ("Campos Novos", "SC", "IFC"),
        ("Mafra", "SC", "IFC"),
        # MS
        ("Paranaíba", "MS", "IFMS"),
        ("Amambaí", "MS", "IFMS"),
        # DF
        ("Sol Nascente", "DF", "IFB"),
        ("Sobradinho", "DF", "IFB"),
    ]

    # Adiciona os novos campi (evitando duplicatas)
    existing = set()
    for item in todas_linhas:
        cidade, uf = item[0], item[1]
        existing.add((cidade.upper(), uf))

    # Mapeamento de siglas curtas para nomes completos de IF
    SIGLA_PARA_IF = {
        "IFAC": "INSTITUTO FEDERAL DO ACRE",
        "IFAL": "INSTITUTO FEDERAL DE ALAGOAS",
        "IFAP": "INSTITUTO FEDERAL DO AMAPÁ",
        "IFAM": "INSTITUTO FEDERAL DO AMAZONAS",
        "IFBA": "INSTITUTO FEDERAL DA BAHIA",
        "IF Baiano": "INSTITUTO FEDERAL BAIANO",
        "IFCE": "INSTITUTO FEDERAL DO CEARÁ",
        "IFB": "INSTITUTO FEDERAL DE BRASÍLIA",
        "IFES": "INSTITUTO FEDERAL DO ESPÍRITO SANTO",
        "IFG": "INSTITUTO FEDERAL DE GOIÁS",
        "IF Goiano": "INSTITUTO FEDERAL GOIANO",
        "IFMA": "INSTITUTO FEDERAL DO MARANHÃO",
        "IFMT": "INSTITUTO FEDERAL DE MATO GROSSO",
        "IFMS": "INSTITUTO FEDERAL DE MATO GROSSO DO SUL",
        "IFMG": "INSTITUTO FEDERAL DE MINAS GERAIS",
        "IFNMG": "INSTITUTO FEDERAL DO NORTE DE MINAS GERAIS",
        "IF Sudeste MG": "INSTITUTO FEDERAL DO SUDESTE DE MINAS GERAIS",
        "IF Sul de Minas": "INSTITUTO FEDERAL DO SUL DE MINAS",
        "IFTM": "INSTITUTO FEDERAL DO TRIÂNGULO MINEIRO",
        "IFPA": "INSTITUTO FEDERAL DO PARÁ",
        "IFPB": "INSTITUTO FEDERAL DA PARAÍBA",
        "IFPR": "INSTITUTO FEDERAL DO PARANÁ",
        "IFPE": "INSTITUTO FEDERAL DE PERNAMBUCO",
        "IF Sertão PE": "INSTITUTO FEDERAL DO SERTÃO PERNAMBUCANO",
        "IFPI": "INSTITUTO FEDERAL DO PIAUÍ",
        "IFF": "INSTITUTO FEDERAL FLUMINENSE",
        "IFRJ": "INSTITUTO FEDERAL DO RIO DE JANEIRO",
        "IFRN": "INSTITUTO FEDERAL DO RIO GRANDE DO NORTE",
        "IFRS": "INSTITUTO FEDERAL DO RIO GRANDE DO SUL",
        "IF Farroupilha": "INSTITUTO FEDERAL FARROUPILHA",
        "IFSul": "INSTITUTO FEDERAL SUL-RIO-GRANDENSE",
        "IFRO": "INSTITUTO FEDERAL DE RONDÔNIA",
        "IFRR": "INSTITUTO FEDERAL DE RORAIMA",
        "IFSC": "INSTITUTO FEDERAL DE SANTA CATARINA",
        "IFC": "INSTITUTO FEDERAL CATARINENSE",
        "IFSP": "INSTITUTO FEDERAL DE SÃO PAULO",
        "IFS": "INSTITUTO FEDERAL DE SERGIPE",
        "IFTO": "INSTITUTO FEDERAL DO TOCANTINS",
        "CEFET-MG": "CENTRO FEDERAL DE EDUCAÇÃO TECNOLÓGICA DE MINAS GERAIS",
        "CEFET-RJ": "CENTRO FEDERAL DE EDUCAÇÃO TECNOLÓGICA CELSO SUCKOW DA FONSECA",
        "CPII": "COLÉGIO PEDRO II",
    }

    added_count = 0
    for cidade, uf, sigla in novos_campi:
        key = (cidade.upper(), uf)
        if key not in existing:
            if_nome_completo = SIGLA_PARA_IF.get(sigla, f"INSTITUTO FEDERAL {sigla}")
            todas_linhas.append((cidade, uf, if_nome_completo, f"CAMPUS {cidade}"))
            existing.add(key)
            added_count += 1

    print(f"  Novos campi adicionados: {added_count}")

    print("\n=== Etapa 3: Limpeza e deduplicação ===\n")

    # Deduplica considerando (municipio, uf, if)
    vistos = set()
    registros_finais = []
    for item in todas_linhas:
        cidade, uf, if_nome, campus_nome = item
        sigla = sigla_if(if_nome)
        chave = (cidade.upper(), uf.upper(), sigla.upper())
        if chave not in vistos:
            vistos.add(chave)
            if sigla in ("CEFET-MG", "CEFET-RJ"):
                tipo = "CEFET"
            elif sigla == "CPII":
                tipo = "CPII"
            else:
                tipo = "IF"
            registros_finais.append({
                "municipio": proper_title(cidade),
                "uf": uf.upper(),
                "instituto_federal": sigla,
                "tipo_instituicao": tipo,
            })

    # Ordena por UF depois municipio
    registros_finais.sort(key=lambda r: (r["uf"], r["municipio"]))

    print(f"  Total de registros únicos: {len(registros_finais)}")
    print(f"  Municípios únicos: {len(set((r['municipio'], r['uf']) for r in registros_finais))}")
    print(f"  Total de IFs distintas: {len(set(r['instituto_federal'] for r in registros_finais))}")

    print(f"\n=== Etapa 4: Salvando CSV ===\n")

    with open(saida, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["municipio", "uf", "instituto_federal", "tipo_instituicao"])
        writer.writeheader()
        writer.writerows(registros_finais)

    print(f"  CSV salvo em: {saida}")
    print(f"  Tamanho: {os.path.getsize(saida):,} bytes")
    print(f"\n=== Resumo Final ===")
    print(f"  Total de campi (linhas no CSV): {len(registros_finais)}")

    # Contagem por UF
    from collections import Counter
    cont_uf = Counter(r["uf"] for r in registros_finais)
    print(f"  Campi por UF:")
    for uf in sorted(cont_uf):
        print(f"    {uf}: {cont_uf[uf]}")


if __name__ == "__main__":
    main()
