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

col = st.sidebar.columns([1,1])
with col[0]:
    cidade_sel = st.sidebar.selectbox("Selecione o Campus:", cidades)

with col[1]:
    componente_sel = st.sidebar.selectbox("Selecione a Área de Conhecimento:", mapa_componentes.keys())



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
    title=f"{cidade_sel}: Evolução da Média ({componente_sel}) das Escolas no ENEM (2014-2024)",
    color_discrete_map=color_discrete_map,
    labels={
        "ANO": "Ano",
        "MEDIA": "Média ENEM",
        "DEPENDENCIA": "Dependência Administrativa"
    }
)

fig.update_traces(
    selector=dict(name=f'Campus {cidade_sel}'),
    line=dict(width=5, color=color_discrete_map[f'Campus {cidade_sel}']),
    marker=dict(size=8, symbol='x', color='yellow'),
)

fig.update_layout(
    xaxis=dict(dtick=1),
    legend_title="Escola/Dependência",
    template="plotly_white",
    hovermode="x unified",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.25,
        xanchor="center",
        x=0.5
    )
)
st.plotly_chart(fig, use_container_width=True)


# --------- Gráfico Violinplot para comparação das médias ---------
st.subheader(f"Comparação das Distribuições das Médias ({componente_sel}) por Rede/Campus")
fig_violin = px.violin(
    df_filt,
    y=mapa_componentes[componente_sel],
    x="LEGENDA",
    color="LEGENDA",
    box=True,
    # points="all",
    color_discrete_map=color_discrete_map,
    labels={
        "LEGENDA": "Escola/Dependência",
        mapa_componentes[componente_sel]: "Média ENEM"
    },
    title=f"{cidade_sel}: Distribuição das Médias ({componente_sel}) por Rede/Campus (2014-2024)"
)
fig_violin.update_layout(
    xaxis_title="Escola/Dependência",
    yaxis_title="Média ENEM",
    template="plotly_white",
    legend_title=None
)
st.plotly_chart(fig_violin, use_container_width=True)

# -----------------------------------------------------
# --------- Informações adicionais ---------



# --------- NOVO: Ranking anual ---------
st.subheader("Ranking das Médias por Rede/Campus (Ano selecionado)")
anos_disponiveis = sorted(df_filt["ANO"].unique())

ano_ranking = st.selectbox("Selecione o Ano para Ranking:", anos_disponiveis, index=len(anos_disponiveis)-1)

df_rank = df_filt[df_filt["ANO"] == ano_ranking]
media_por_legenda = df_rank.groupby("LEGENDA")[mapa_componentes[componente_sel]].mean().reset_index()
media_por_legenda = media_por_legenda.sort_values(by=mapa_componentes[componente_sel], ascending=False)
fig_rank = px.bar(
    media_por_legenda,
    x=mapa_componentes[componente_sel],
    y="LEGENDA",
    orientation='h',
    color="LEGENDA",
    color_discrete_map=color_discrete_map,
    title=f"Ranking das Médias por Rede/Campus ({componente_sel}, {ano_ranking})",
    labels={
        mapa_componentes[componente_sel]: "Média ENEM",
        "LEGENDA": "Escola/Dependência"
    }
)
st.plotly_chart(fig_rank, use_container_width=True)

# --------- NOVO: Boxplot por ano com média do Campus ---------
st.subheader("Dispersão das Médias por Rede/Campus ao longo dos anos")
fig_box = px.box(
    df_filt,
    x="ANO",
    y=mapa_componentes[componente_sel],
    color="LEGENDA",
    # points="all",
    color_discrete_map=color_discrete_map,
    title=f"Dispersão das Médias por Rede/Campus ({componente_sel}) ao longo dos anos",
    labels={
        "ANO": "Ano",
        mapa_componentes[componente_sel]: "Média ENEM"
    }
)
# Adiciona linha da média do campus IFMG
if f'Campus {cidade_sel}' in df_filt['LEGENDA'].unique():
    media_ifmg = df_filt[df_filt['LEGENDA']==f'Campus {cidade_sel}'].groupby('ANO')[mapa_componentes[componente_sel]].mean()
    fig_box.add_scatter(
        x=media_ifmg.index, 
        y=media_ifmg.values,
        mode="lines+markers",
        line=dict(color="#15ac15", width=4, dash='dot'),
        name=f"Média Campus {cidade_sel}"
    )
st.plotly_chart(fig_box, use_container_width=True)

# --------- NOVO: Gap IFMG vs. Redes ---------
st.subheader("Diferença (GAP) entre Campus IFMG e demais Redes por Ano")
gap_df = df_filt.pivot_table(
    index='ANO', 
    columns='LEGENDA', 
    values=mapa_componentes[componente_sel],
    aggfunc='mean'
).reset_index()
for rede in ['Rede Estadual','Rede Municipal','Rede Privada']:
    if f'Campus {cidade_sel}' in gap_df.columns and rede in gap_df.columns:
        gap_df[f"GAP {rede}"] = gap_df[f'Campus {cidade_sel}'] - gap_df[rede]
gap_cols = [col for col in gap_df.columns if col.startswith('GAP')]
fig_gap = px.line(
    gap_df,
    x='ANO',
    y=gap_cols,
    markers=True,
    title=f"GAP da Média do Campus {cidade_sel} em relação às Redes ({componente_sel})",
    labels={"value": "Diferença da Média (Campus - Rede)", "variable":"Rede"},
)
fig_gap.update_layout(
    template="plotly_white",
    xaxis=dict(dtick=1),
    yaxis_title="Diferença da Média",
    legend_title="GAP vs Rede"
)
st.plotly_chart(fig_gap, use_container_width=True)


# --------- Informações adicionais ---------


# --------- Dados filtrados ---------
with st.expander("Ver tabela de dados filtrados", expanded=False):
    st.dataframe(df_filt, use_container_width=True)




# comparando todo o IFMG com as redes

st.markdown("---")

st.header("Comparação: IFMG (todos os campi juntos) vs Redes")

# 1. Adiciona uma coluna 'GRUPO' no dataframe geral
df_grupo = df.copy()
df_grupo['GRUPO'] = df_grupo.apply(
    lambda row: "IFMG" if (row['SG_UF_ESC']=="MG" and row['NO_MUNICIPIO_ESC'] in cidades_ifmg and row['DEPENDENCIA']=="Federal") else f"Rede {row['DEPENDENCIA']}",
    axis=1
)

# Garante só as redes relevantes (descarta federal fora do IFMG, se houver)
redes_validas = ['IFMG', 'Rede Estadual', 'Rede Municipal', 'Rede Privada']
df_grupo = df_grupo[df_grupo['GRUPO'].isin(redes_validas)]

# 2. Linha de tendência das médias anuais
medias_anuais = df_grupo.groupby(['ANO','GRUPO'])[mapa_componentes[componente_sel]].mean().reset_index()
fig_grupo_linha = px.line(
    medias_anuais,
    x="ANO", y=mapa_componentes[componente_sel],
    color="GRUPO",
    markers=True,
    title=f"Evolução das Médias ({componente_sel}) - IFMG (todos campi) vs Redes",
    labels={"ANO": "Ano", mapa_componentes[componente_sel]: "Média ENEM", "GRUPO":"Rede"},
    color_discrete_map={
        'IFMG': '#15ac15', 'Rede Estadual': '#ff7f0e', 'Rede Municipal': '#1f77b4', 'Rede Privada': '#d62728'
    }
)
fig_grupo_linha.update_layout(template="plotly_white", xaxis=dict(dtick=1))
st.plotly_chart(fig_grupo_linha, use_container_width=True)

# 3. Boxplot/Violinplot das médias (todos os anos juntos)
st.subheader("Distribuição das Médias por Rede (todos os anos)")
fig_grupo_box = px.violin(
    df_grupo,
    x="GRUPO",
    y=mapa_componentes[componente_sel],
    color="GRUPO",
    box=True, 
    # points="all",
    color_discrete_map={
        'IFMG': '#15ac15', 'Rede Estadual': '#ff7f0e', 'Rede Municipal': '#1f77b4', 'Rede Privada': '#d62728'
    },
    labels={"GRUPO":"Rede", mapa_componentes[componente_sel]:"Média ENEM"},
    title=f"Distribuição das Médias ({componente_sel}) por Rede (2014-2024)"
)
fig_grupo_box.update_layout(template="plotly_white")
st.plotly_chart(fig_grupo_box, use_container_width=True)

# 4. Ranking das médias por rede para um ano escolhido
st.subheader("Ranking das Médias por Rede (Ano Selecionado)")
anos_grupo = sorted(df_grupo["ANO"].unique())
ano_grupo = st.selectbox("Ano para comparação de redes:", anos_grupo, key="ano_grupo", index=len(anos_grupo)-1)
df_rank_grupo = df_grupo[df_grupo["ANO"] == ano_grupo]
media_rede_ano = df_rank_grupo.groupby("GRUPO")[mapa_componentes[componente_sel]].mean().reset_index()
media_rede_ano = media_rede_ano.sort_values(by=mapa_componentes[componente_sel], ascending=False)
fig_grupo_rank = px.bar(
    media_rede_ano,
    x=mapa_componentes[componente_sel], y="GRUPO",
    orientation='h',
    color="GRUPO",
    color_discrete_map={
        'IFMG': '#15ac15', 'Rede Estadual': '#ff7f0e', 'Rede Municipal': '#1f77b4', 'Rede Privada': '#d62728'
    },
    title=f"Ranking das Médias por Rede ({componente_sel}, {ano_grupo})",
    labels={mapa_componentes[componente_sel]: "Média ENEM", "GRUPO": "Rede"}
)
st.plotly_chart(fig_grupo_rank, use_container_width=True)





st.markdown("---")
st.markdown("Desenvolvido a partir dos microdados do ENEM 2014-2024 disponibilizados pelo INEP em [gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem).")
st.markdown("---")
st.caption("Desenvolvido por [Luciano Espiridiao](luciano.espiriao@ifmg.edu.br). 2025 - Todos os direitos reservados.")

