import streamlit as st
import pandas as pd
import plotly.express as px

# --------- Configurações iniciais ---------
st.set_page_config(page_title="Evolução da Média no ENEM por Campus do IFMG", layout="wide")

st.title("Evolução da Média no ENEM por Campus do IFMG (2014-2024)")

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

col = st.columns([2,4])
with col[0]:
    cidade_sel = st.selectbox("Selecione a cidade:", cidades)

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
    y="MEDIA",
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
    line=dict(width=4, color=color_discrete_map[f'Campus {cidade_sel}']),
    marker=dict(size=8)
)

st.plotly_chart(fig, use_container_width=True)


# --------- Dados filtrados ---------
with st.expander("Ver tabela de dados filtrados", expanded=False):
    st.dataframe(df_filt, use_container_width=True)



# st.caption("Desenvolvido com ❤️ por Luciano Espiridiao. 2025 - Todos os direitos reservados.")

