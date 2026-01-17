# ENEM (IFMG vs Redes) — 2014–2024

Aplicativo e notebooks para explorar a **evolução das médias do ENEM** (por área de conhecimento e média geral) para **campi do IFMG** e comparar com as redes **Estadual, Municipal e Privada**, usando dados consolidados a partir dos **microdados do INEP**.

O projeto inclui:

- Um app **Streamlit** ([app.py](app.py)) com gráficos interativos (Plotly).
- Um dataset consolidado ([enens2014-2024.csv](enens2014-2024.csv)) pronto para consumo pelo app.
- Pastas com microdados por ano (ex.: `microdados_enem_2014/`, `microdados_enem_2024/`) e scripts/dicionários oficiais.
- Notebooks usados para gerar rankings anuais e consolidar o CSV final.

> Data de referência do projeto no contexto atual: 17 de janeiro de 2026.

---

## Como rodar o app (Streamlit)

### 1) Criar ambiente e instalar dependências

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Executar

```bash
streamlit run app.py
```

O Streamlit abrirá uma URL local (geralmente `http://localhost:8501`).

---

## O que o app faz

O app ([app.py](app.py)) lê o arquivo [enens2014-2024.csv](enens2014-2024.csv) (separador `;`) e permite:

1. **Selecionar um campus (município)** do IFMG (lista fixa de municípios em MG).
2. **Selecionar uma área de conhecimento**:
	 - Média (coluna `MEDIA`)
	 - Linguagens, Códigos e suas Tecnologias (`LC`)
	 - Ciências Humanas e suas Tecnologias (`CH`)
	 - Ciências da Natureza e suas Tecnologias (`CN`)
	 - Matemática e suas Tecnologias (`MT`)
	 - Redação (`RD`)

Para o campus escolhido, o app:

- Plota **linha temporal** (2014–2024) da média por rede/campus.
- Plota **violin plot** para comparar distribuições das médias por rede/campus.
- Exibe **ranking horizontal** das médias por rede/campus em um **ano selecionado**.
- Exibe **boxplot ao longo do tempo** e adiciona a linha da média do campus.
- Calcula e plota o **GAP (Campus − Rede)** por ano para Estadual/Municipal/Privada.
- Traz uma seção adicional:
	- **IFMG (todos os campi juntos) vs Redes**: linha de tendência, distribuição e ranking por ano.

---

## Dataset consolidado (enens2014-2024.csv)

Arquivo central do projeto: [enens2014-2024.csv](enens2014-2024.csv)

- Formato: CSV separado por `;`
- Linhas: ~89k (varia conforme critérios de geração)
- Granularidade: **município × dependência administrativa × ano**

### Esquema (colunas)

| Coluna | Tipo | Descrição |
|---|---:|---|
| `POSICAO` | int | Posição no ranking (ordem decrescente por `MEDIA`) dentro do ano na fonte consolidada. |
| `NO_MUNICIPIO_ESC` | str | Município da escola (nome). |
| `SG_UF_ESC` | str | UF da escola (ex.: `MG`). |
| `DEPENDENCIA` | str | Dependência administrativa: `Federal`, `Estadual`, `Municipal`, `Privada`. |
| `ALUNOS` | int | Quantidade agregada de participantes considerados. |
| `LC` | float | Média (ou medida agregada) em Linguagens. |
| `CH` | float | Média em Ciências Humanas. |
| `CN` | float | Média em Ciências da Natureza. |
| `MT` | float | Média em Matemática. |
| `RD` | float | Média em Redação. |
| `MEDIA` | float | Média geral (média das 5 notas). |
| `ANO` | int | Ano (2014 a 2024). |

### Observações importantes

- O CSV consolidado **não** contém colunas como `LOCALIZACAO` ou `CO_ESCOLA`. Alguns notebooks exploram essas dimensões, mas o arquivo final foi normalizado para uso direto no app.
- Os microdados do INEP são grandes e normalmente vêm em **latin1** e com separador `;` (os notebooks fazem leitura com `encoding='latin1'`).

---

## Rankings anuais (por pasta de ano)

Em cada pasta `microdados_enem_<ANO>/DADOS/` podem existir arquivos de ranking auxiliares, por exemplo:

- 2014: `microdados_enem_2014/DADOS/ranking_escolas_enem2014.csv`
	- Cabeçalho atual (exemplo): `POSICAO;NO_MUNICIPIO_ESC;SG_UF_ESC;DEPENDENCIA;ALUNOS;LC;CH;CN;MT;RD;MEDIA`
- 2024: `microdados_enem_2024/DADOS/ranking_escolas_enem2024.csv`
	- Cabeçalho atual (exemplo): `POSICAO;CO_ESCOLA;NO_MUNICIPIO_ESC;SG_UF_ESC;DEPENDENCIA;ALUNOS;LC;CH;CN;MT;RD;MEDIA`

O notebook de 2024 ([2024.ipynb](2024.ipynb)) mostra a leitura de `microdados_enem_2024/DADOS/RESULTADOS_2024.csv` e a geração desse ranking.

---

## Notebooks (o que cada um contém)

- [Streamlit.ipynb](Streamlit.ipynb)
	- Rascunho/protótipo do app e dos gráficos.
	- Mostra execução via `!streamlit run app.py`.

- [Explorando.ipynb](Explorando.ipynb)
	- Explorações e rotinas para gerar rankings (principalmente 2014–2023) e consolidar em `enens2014-2024.csv`.
	- Inclui funções como `cria_ranking_por_dependencia` e `juntar_salvar()`.
	- Atenção: há células que referenciam `LOCALIZACAO`, mas o CSV consolidado atual não traz essa coluna.

- [2024.ipynb](2024.ipynb)
	- Funções auxiliares para sumarização e ranking.
	- Geração do ranking 2024 a partir de `RESULTADOS_2024.csv`.

- [Untitled.ipynb](Untitled.ipynb)
	- Exemplo mais “didático” de leitura de microdados e agregações.
	- Define `ler_microdados(ano, tipo_analise)` com filtros de notas válidas e geração de ranking.

---

## Estrutura do repositório

Visão geral (nível alto):

```text
.
├── app.py
├── requirements.txt
├── enens2014-2024.csv
├── 2024.ipynb
├── Explorando.ipynb
├── Streamlit.ipynb
├── Untitled.ipynb
├── microdados_enem_2009/
├── microdados_enem_2010/
├── ...
├── microdados_enem_2024/
└── microdados_enem_por_escola/
```

Dentro de cada `microdados_enem_<ANO>/` normalmente existem:

- `DADOS/`: CSVs grandes (microdados) e arquivos derivados (rankings).
- `DICIONÁRIO/`: dicionários de dados do INEP.
- `INPUTS/`: scripts de leitura (R/SPSS/SAS) fornecidos pelo INEP.
- `LEIA-ME E DOCUMENTOS TÉCNICOS/`: documentação oficial.
- `PROVAS E GABARITOS/`: provas e gabaritos.

---

## Sobre versionamento e arquivos grandes

O arquivo [.gitignore](.gitignore) ignora pastas `microdados_enem*/*` e notebooks (`*.ipynb`). Isso é útil porque:

- Os microdados são muito grandes.
- Notebooks frequentemente geram diffs enormes.

Se você pretende versionar notebooks, ajuste o `.gitignore` conforme necessário.

---

## Fonte dos dados

Os dados de base vêm dos microdados do ENEM disponibilizados pelo INEP:

- https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem

---

## Créditos

O app exibe no rodapé:

- “Desenvolvido a partir dos microdados do ENEM 2014-2024 disponibilizados pelo INEP …”
- Autor: Luciano Espiridiao (contato no rodapé do app)

