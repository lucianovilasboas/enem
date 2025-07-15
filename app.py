import streamlit as st
import pandas as pd
import plotly.express as px

# --------- Configurações iniciais ---------
st.set_page_config(page_title="Evolução da Média no ENEM por Campus do IFMG", layout="wide")

st.title("Evolução da Média no ENEM por Campus do IFMG (2014-2024)")

st.markdown("""
Este aplicativo permite visualizar a evolução da média das escolas do ENEM para os campi do IFMG e comparar 
com as redes Estadual, Municipal e Privada.
Selecione o campus e a área de conhecimento para ver os dados.
""")

# --------- Leitura do CSV ---------
# Substitua pelo caminho correto do seu arquivo
csv_file = 'enens2014-2024.csv'
df = pd.read_csv(csv_file, sep=';')

# Corrige possíveis espaços nos nomes das colunas
df.columns = df.columns.str.strip()

# --------- Filtros ---------

cidades_ifmg = [
    "Conselheiro Lafaiete",
    "Piumhi",
    "Ipatinga",
    "Itabirito",
    "Ponte Nova",
    "Formiga",
    "Bambuí",
    "Betim",
    "Ibirité",
    "Congonhas",
    "Governador Valadares",
    "Ouro Branco",
    "Ouro Preto",
    "Ribeirão das Neves",
    "Sabará",
    "Santa Luzia",
    "São João Evangelista",
    "Arcos",
]

cidades = sorted(cidades_ifmg)
mapa_componentes = dict([('Média','MEDIA'), 
                ('Linguagens, Códigos e suas Tecnologias','LC'), 
                ('Ciências Humanas e suas Tecnologias','CH'), 
                ('Ciências da Natureza e suas Tecnologias','CN'),
                ('Matemática e suas Tecnologias', 'MT'), 
                ('Redação','RD')])

col = st.columns([1,1])
with col[0]:
    cidade_sel = st.selectbox("Selecione o Campus:", cidades)

with col[1]:
    componente_sel = st.selectbox("Selecione a Área de Conhecimento:", mapa_componentes.keys())



df_filt = df[
    (df['NO_MUNICIPIO_ESC']== cidade_sel) & (df['SG_UF_ESC'] == 'MG') 
].copy()

# --------- Coluna personalizada para legenda ---------
df_filt['LEGENDA'] = df_filt['DEPENDENCIA'].apply(
    lambda d: f'Campus {cidade_sel}' if d == 'Federal' else f'Rede {d}'
)
# --------- Remoção de colunas desnecessárias ---------
df_filt = df_filt.drop(columns=['DEPENDENCIA','POSICAO'])

# --------- Cores fixas para Dependência/Campus ---------
color_discrete_map = {
    f'Campus {cidade_sel}': "#15ac15",    # verde
    'Rede Estadual': '#ff7f0e',                # laranja
    'Rede Municipal': '#1f77b4',               # azul
    'Rede Privada': '#d62728'                  # vermelho
}

# --------- Gráfico ---------
fig = px.line(
    df_filt,
    x="ANO",
    y=mapa_componentes[componente_sel],
    color="LEGENDA",
    markers=True,
    title=f"{cidade_sel}: Evolução da Média das Escolas no ENEM (2014-2024)",
    color_discrete_map=color_discrete_map,
    labels={
        "ANO": "Ano",
        "MEDIA": "Média ENEM",
        "DEPENDENCIA": "Dependência Administrativa"
    }
)

fig.update_layout(
    xaxis=dict(dtick=1),
     legend_title="Escola/Dependência",
    template="plotly_white",
    hovermode="x unified"
)

fig.update_traces(
    selector=dict(name=f'Campus {cidade_sel}'),
    line=dict(width=5, color=color_discrete_map[f'Campus {cidade_sel}']),
    marker=dict(size=8, symbol='x', color='black'),
)

st.plotly_chart(fig, use_container_width=True)


# --------- Dados filtrados ---------
with st.expander("Ver tabela de dados filtrados", expanded=False):
    st.dataframe(df_filt, use_container_width=True)



st.markdown("---")
st.markdown("#### Desenvolvido a partir dos microdados do ENEM 2014-2024 disponibilizados pelo INEP em [gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem).")
st.markdown("---")
st.caption("Desenvolvido por [Luciano Espiridiao](luciano.espiriao@ifmg.edu.br). 2025 - Todos os direitos reservados.")

