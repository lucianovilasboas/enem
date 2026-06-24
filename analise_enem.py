import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
import unicodedata
from glob import glob
import re

st.set_page_config(page_title="ENEM - Análise Comparativa", layout="wide")
st.title("Evolução do ENEM por Nível Agregado (2014-2025)")
st.markdown("Comparação das médias: **Nacional**, **Estado**, **Município** e **Rede Federal** ao longo dos anos.")


@st.cache_data
def carregar_dados():
    arquivos = sorted(glob("dados/ranking_escolas_enem*.csv"))
    dfs = []
    for arq in arquivos:
        ano = int(re.search(r"(\d{4})", arq).group(1))
        df = pd.read_csv(arq, sep=";", decimal=",")
        df.columns = df.columns.str.strip()
        if "CO_ESCOLA" in df.columns:
            df.drop(columns=["CO_ESCOLA"], inplace=True)
        if "LOCALIZACAO" not in df.columns:
            df["LOCALIZACAO"] = None
        df["ANO"] = ano
        dfs.append(df)
    df = pd.concat(dfs, ignore_index=True)
    df["MEDIA"] = pd.to_numeric(df["MEDIA"], errors="coerce")
    df["DEPENDENCIA"] = df["DEPENDENCIA"].str.strip().str.title()
    df["SG_UF_ESC"] = df["SG_UF_ESC"].str.strip().str.upper()
    df["NO_MUNICIPIO_ESC"] = df["NO_MUNICIPIO_ESC"].str.strip().str.title()
    return df


df = carregar_dados()

# Sidebar para filtros
st.sidebar.header("🔍 Filtros")
anos_disponiveis = sorted(df["ANO"].unique())
anos_sel = st.sidebar.slider("Intervalo de anos", min_value=int(min(anos_disponiveis)), max_value=int(max(anos_disponiveis)), value=(2014, 2025))

ufs = sorted(df["SG_UF_ESC"].unique())
uf_sel = st.sidebar.multiselect("🗺️ Estado(s)", ufs, default=[])

municipios = sorted(df["NO_MUNICIPIO_ESC"].unique())
mun_sel = st.sidebar.multiselect("🏙️ Município(s)", municipios, default=[])

df_filtrado = df[(df["ANO"] >= anos_sel[0]) & (df["ANO"] <= anos_sel[1])]
if uf_sel:
    df_filtrado = df_filtrado[df_filtrado["SG_UF_ESC"].isin(uf_sel)]
if mun_sel:
    df_filtrado = df_filtrado[df_filtrado["NO_MUNICIPIO_ESC"].isin(mun_sel)]

# ---- Média Nacional ----
media_nacional = df_filtrado.groupby("ANO")["MEDIA"].mean().reset_index()
media_nacional.columns = ["ANO", "MEDIA"]
media_nacional["NIVEL"] = "Nacional"

# ---- Média por Estado ----
media_estado = df_filtrado.groupby(["ANO", "SG_UF_ESC"])["MEDIA"].mean().reset_index()
media_estado.columns = ["ANO", "SG_UF_ESC", "MEDIA"]
media_estado["NIVEL"] = "Estado"

# ---- Média por Município ----
media_municipio = df_filtrado.groupby(["ANO", "NO_MUNICIPIO_ESC", "SG_UF_ESC"])["MEDIA"].mean().reset_index()
media_municipio.columns = ["ANO", "NO_MUNICIPIO_ESC", "SG_UF_ESC", "MEDIA"]
media_municipio["NIVEL"] = "Município"

# ---- Média Rede Federal ----
df_federal = df_filtrado[df_filtrado["DEPENDENCIA"] == "Federal"]
media_federal = df_federal.groupby("ANO")["MEDIA"].mean().reset_index()
media_federal.columns = ["ANO", "MEDIA"]
media_federal["NIVEL"] = "Rede Federal"

# ---- Comparação geral (todas as linhas) ----
st.subheader("📈 Evolução da Média Geral")
fig = px.line(media_nacional, x="ANO", y="MEDIA", markers=True, title="Média Nacional")
fig.update_layout(yaxis_range=[min(df["MEDIA"]), max(df["MEDIA"])])
st.plotly_chart(fig, use_container_width=True)

# ---- Grid de comparação ----
abas = st.tabs(["Nacional x Rede Federal", "Por Estado", "Por Município"])

with abas[0]:
    st.subheader("⚖️ Nacional vs Rede Federal")
    comp = pd.concat([
        media_nacional[["ANO", "MEDIA", "NIVEL"]],
        media_federal[["ANO", "MEDIA", "NIVEL"]],
    ], ignore_index=True)
    fig2 = px.line(comp, x="ANO", y="MEDIA", color="NIVEL", markers=True,
                   title="Comparação: Nacional x Rede Federal")
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("📊 Diferença (Rede Federal - Nacional)")
    merged = media_nacional.merge(media_federal, on="ANO", suffixes=("_nac", "_fed"))
    merged["DIFERENCA"] = merged["MEDIA_fed"] - merged["MEDIA_nac"]
    fig_diff = px.bar(merged, x="ANO", y="DIFERENCA",
                      title="Diferença da média da Rede Federal em relação à Nacional",
                      color="DIFERENCA", color_continuous_scale="RdYlGn")
    st.plotly_chart(fig_diff, use_container_width=True)

with abas[1]:
    st.subheader("🌍 Média por Estado ao longo dos anos")
    if uf_sel:
        fig3 = px.line(media_estado, x="ANO", y="MEDIA", color="SG_UF_ESC", markers=True)
        st.plotly_chart(fig3, use_container_width=True)

        # Heatmap
        heat = media_estado.pivot(index="SG_UF_ESC", columns="ANO", values="MEDIA")
        fig_heat = px.imshow(heat, text_auto=".0f", aspect="auto",
                             title="Mapa de Calor - Média por Estado/Ano",
                             color_continuous_scale="viridis")
        st.plotly_chart(fig_heat, use_container_width=True)
    else:
        estados_top = media_estado.groupby("SG_UF_ESC")["MEDIA"].mean().sort_values(ascending=False).head(10).index
        df_top = media_estado[media_estado["SG_UF_ESC"].isin(estados_top)]
        fig3 = px.line(df_top, x="ANO", y="MEDIA", color="SG_UF_ESC", markers=True,
                       title="Top 10 Estados por média geral")
        st.plotly_chart(fig3, use_container_width=True)

with abas[2]:
    st.subheader("🏙️ Média por Município ao longo dos anos")
    if mun_sel:
        fig4 = px.line(media_municipio, x="ANO", y="MEDIA",
                       color="NO_MUNICIPIO_ESC", line_dash="SG_UF_ESC", markers=True)
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.info("Selecione um ou mais municípios no filtro lateral para visualizar.")

# ---- Análise da Rede Federal ----
st.subheader("🔬 Análise Detalhada — Rede Federal")
st.markdown("Filtrando apenas escolas com dependência **Federal**.")

tab_if, tab_top = st.tabs(["Evolução Rede Federal", "Top Escolas Federais por Ano"])

with tab_if:
    if not df_federal.empty:
        fig_fed = px.line(media_federal, x="ANO", y="MEDIA", markers=True,
                          title="Média das Escolas Federais no ENEM")
        st.plotly_chart(fig_fed, use_container_width=True)

        media_fed_uf = df_federal.groupby(["ANO", "SG_UF_ESC"])["MEDIA"].mean().reset_index()
        fig_fed_uf = px.line(media_fed_uf, x="ANO", y="MEDIA", color="SG_UF_ESC", markers=True,
                             title="Média das Escolas Federais por Estado")
        st.plotly_chart(fig_fed_uf, use_container_width=True)
    else:
        st.warning("Nenhum dado da Rede Federal no recorte selecionado.")

with tab_top:
    ano_sel = st.selectbox("📅 Selecione o ano", anos_disponiveis)
    top_n = st.slider("Quantas escolas?", 1, 20, 10)
    df_ano = df_filtrado[df_filtrado["ANO"] == ano_sel].copy()
    top_escolas = df_ano.sort_values("MEDIA", ascending=False).head(top_n)
    fig_top = px.bar(top_escolas, x="MEDIA", y="NO_MUNICIPIO_ESC",
                     color="DEPENDENCIA", orientation="h",
                     title=f"Top {top_n} escolas em {ano_sel}",
                     text_auto=".1f")
    fig_top.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_top, use_container_width=True)

    st.dataframe(top_escolas[["POSICAO", "NO_MUNICIPIO_ESC", "SG_UF_ESC", "DEPENDENCIA", "ALUNOS", "MEDIA"]])

# ---- Mapa do Brasil ----
st.subheader("🗺️ Mapa do Brasil")
st.markdown("Visualização geográfica das médias do ENEM por **Estado** e por **Município**.")

tab_mapa_estado, tab_mapa_mun = st.tabs(["Por Estado (Coroplético)", "Por Município (Mapa de Bolhas)"])

with tab_mapa_estado:
    ano_mapa = st.selectbox("📅 Selecione o ano para o mapa", anos_disponiveis, key="ano_mapa_estado")
    media_uf_ano = df_filtrado[df_filtrado["ANO"] == ano_mapa].groupby("SG_UF_ESC")["MEDIA"].mean().reset_index()

    @st.cache_data(ttl=3600)
    def carregar_geojson_estados():
        url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
        try:
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return None

    geojson_estados = carregar_geojson_estados()

    if geojson_estados is not None:
        fig_mapa_estado = px.choropleth(
            media_uf_ano,
            geojson=geojson_estados,
            locations="SG_UF_ESC",
            featureidkey="properties.sigla",
            color="MEDIA",
            hover_name="SG_UF_ESC",
            color_continuous_scale="RdYlGn_r",
            range_color=[media_uf_ano["MEDIA"].min(), media_uf_ano["MEDIA"].max()],
            title=f"Média ENEM por Estado — {ano_mapa}",
        )
        fig_mapa_estado.update_geos(fitbounds="locations", visible=True)
        fig_mapa_estado.update_layout(margin=dict(l=0, r=0, t=40, b=0), height=500)
        st.plotly_chart(fig_mapa_estado, use_container_width=True)
    else:
        st.error("Não foi possível carregar o mapa dos estados.")

    st.dataframe(
        media_uf_ano.sort_values("MEDIA", ascending=False)
        .reset_index(drop=True)
        .rename(columns={"SG_UF_ESC": "Estado", "MEDIA": "Média"})
        .style.format({"Média": "{:.2f}"})
    )

with tab_mapa_mun:
    ano_mapa_mun = st.selectbox("📅 Selecione o ano", anos_disponiveis, key="ano_mapa_mun")
    qtd_mun = st.slider("Quantidade de municípios", 10, 200, 80)

    media_mun_ano = (
        df_filtrado[df_filtrado["ANO"] == ano_mapa_mun]
        .groupby(["NO_MUNICIPIO_ESC", "SG_UF_ESC"])["MEDIA"]
        .mean()
        .reset_index()
    )

    @st.cache_data(ttl=3600)
    def carregar_geojson_municipios():
        url = "https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-100-mun.json"
        try:
            r = requests.get(url, timeout=30)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return None

    geojson_mun = carregar_geojson_municipios()

    if geojson_mun is not None:
        gj_names = {}
        for f in geojson_mun["features"]:
            raw = f["properties"]["name"]
            key = unicodedata.normalize("NFKD", raw).encode("ASCII", "ignore").decode().strip().lower()
            gj_names[key] = raw

        media_mun_ano["GEOJSON_NAME"] = (
            media_mun_ano["NO_MUNICIPIO_ESC"]
            .str.strip()
            .str.lower()
            .map(lambda x: unicodedata.normalize("NFKD", x).encode("ASCII", "ignore").decode())
            .map(gj_names)
        )

        mun_com_geo = media_mun_ano.dropna(subset=["GEOJSON_NAME"]).nlargest(qtd_mun, "MEDIA")

        if not mun_com_geo.empty:
            fig_mun = px.choropleth_mapbox(
                mun_com_geo,
                geojson=geojson_mun,
                locations="GEOJSON_NAME",
                featureidkey="properties.name",
                color="MEDIA",
                color_continuous_scale="RdYlGn_r",
                mapbox_style="carto-positron",
                zoom=2.8,
                center=dict(lat=-14.2, lon=-51.9),
                opacity=0.7,
                hover_data={"NO_MUNICIPIO_ESC": True, "SG_UF_ESC": True, "MEDIA": ":.2f"},
                title=f"Média ENEM por Município — {ano_mapa_mun} (top {qtd_mun})",
            )
            fig_mun.update_layout(margin=dict(l=0, r=0, t=40, b=0), height=550)
            st.plotly_chart(fig_mun, use_container_width=True)
        else:
            st.warning("Nenhum município encontrado no GeoJSON para este ano.")
    else:
        st.warning("Não foi possível carregar o GeoJSON dos municípios. Exibindo treemap como alternativa.")

    fig_tree = px.treemap(
        media_mun_ano,
        path=["SG_UF_ESC", "NO_MUNICIPIO_ESC"],
        values="MEDIA",
        color="MEDIA",
        color_continuous_scale="RdYlGn_r",
        title=f"Municípios agrupados por Estado — {ano_mapa_mun}",
    )
    fig_tree.update_layout(margin=dict(l=0, r=0, t=40, b=0), height=500)
    st.plotly_chart(fig_tree, use_container_width=True)

    top_mun = media_mun_ano.nlargest(qtd_mun, "MEDIA")
    st.caption(f"Top {qtd_mun} municípios por média em {ano_mapa_mun}:")
    st.dataframe(
        top_mun[["NO_MUNICIPIO_ESC", "SG_UF_ESC", "MEDIA"]]
        .reset_index(drop=True)
        .rename(columns={"NO_MUNICIPIO_ESC": "Município", "SG_UF_ESC": "UF", "MEDIA": "Média"})
        .style.format({"Média": "{:.2f}"})
    )

# ---- Tabelas Resumo ----
st.subheader("📋 Tabelas Resumo")
with st.expander("Média Nacional por Ano"):
    st.dataframe(media_nacional.set_index("ANO").style.format("{:.2f}", subset=["MEDIA"]))

with st.expander("Média Rede Federal por Ano"):
    if not media_federal.empty:
        st.dataframe(media_federal.set_index("ANO").style.format("{:.2f}", subset=["MEDIA"]))

with st.expander("Média por Estado e Ano (matriz)"):
    pivot_estado = media_estado.pivot(index="SG_UF_ESC", columns="ANO", values="MEDIA")
    st.dataframe(pivot_estado.style.format("{:.1f}"))

st.caption("Fonte: Dados do ENEM (INEP) — ranking por escola.")
