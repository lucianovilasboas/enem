import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
import unicodedata
from glob import glob
import re

st.set_page_config(page_title="ENEM - Mapa por Rede", layout="wide")
st.title("ENEM por Município e Rede de Ensino")
st.markdown(
    "Comparação das médias entre as redes **Federal**, **Estadual**, **Municipal** e **Privada** "
    "por município, estado e Brasil."
)


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
        df["ANO"] = ano
        dfs.append(df)
    df = pd.concat(dfs, ignore_index=True)
    df["MEDIA"] = pd.to_numeric(df["MEDIA"], errors="coerce")
    df["DEPENDENCIA"] = df["DEPENDENCIA"].str.strip().str.title()
    df["SG_UF_ESC"] = df["SG_UF_ESC"].str.strip().str.upper()
    df["NO_MUNICIPIO_ESC"] = df["NO_MUNICIPIO_ESC"].str.strip().str.title()
    return df


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


df = carregar_dados()
geojson_estados = carregar_geojson_estados()
geojson_mun = carregar_geojson_municipios()

# Sidebar
st.sidebar.header("🔍 Filtros")
anos = sorted(df["ANO"].unique())
ano_sel = st.sidebar.selectbox("📅 Ano", anos)

redes = sorted(df["DEPENDENCIA"].unique())
rede_sel = st.sidebar.multiselect("🏫 Rede(s)", redes, default=redes)

ufs = sorted(df["SG_UF_ESC"].unique())
uf_sel = st.sidebar.multiselect("🗺️ Estado(s)", ufs, default=[])

# Filtrar
filtro = df["ANO"] == ano_sel
if rede_sel:
    filtro &= df["DEPENDENCIA"].isin(rede_sel)
if uf_sel:
    filtro &= df["SG_UF_ESC"].isin(uf_sel)
df_ano = df[filtro].copy()

# Agregações
# Nacional por rede
nac_rede = df_ano.groupby("DEPENDENCIA")["MEDIA"].agg(["mean", "count"]).reset_index()
nac_rede.columns = ["DEPENDENCIA", "MEDIA_NAC", "ESCOLAS_NAC"]

# Estado por rede
est_rede = df_ano.groupby(["SG_UF_ESC", "DEPENDENCIA"])["MEDIA"].agg(["mean", "count"]).reset_index()
est_rede.columns = ["SG_UF_ESC", "DEPENDENCIA", "MEDIA_EST", "ESCOLAS_EST"]

# Municipio por rede
mun_rede = df_ano.groupby(["NO_MUNICIPIO_ESC", "SG_UF_ESC", "DEPENDENCIA"])["MEDIA"].agg(["mean", "count"]).reset_index()
mun_rede.columns = ["NO_MUNICIPIO_ESC", "SG_UF_ESC", "DEPENDENCIA", "MEDIA_MUN", "ESCOLAS_MUN"]

# Juntar tudo
comp = mun_rede.merge(est_rede, on=["SG_UF_ESC", "DEPENDENCIA"], how="left")
comp = comp.merge(nac_rede, on=["DEPENDENCIA"], how="left")
comp["DIF_ESTADO"] = comp["MEDIA_MUN"] - comp["MEDIA_EST"]
comp["DIF_NACIONAL"] = comp["MEDIA_MUN"] - comp["MEDIA_NAC"]

# GEOJSON name matching for municipalities
if geojson_mun is not None:
    gj_names = {}
    for f in geojson_mun["features"]:
        raw = f["properties"]["name"]
        key = unicodedata.normalize("NFKD", raw).encode("ASCII", "ignore").decode().strip().lower()
        gj_names[key] = raw
    comp["GEOJSON_NAME"] = (
        comp["NO_MUNICIPIO_ESC"]
        .str.strip()
        .str.lower()
        .map(lambda x: unicodedata.normalize("NFKD", x).encode("ASCII", "ignore").decode())
        .map(gj_names)
    )


# ---- MAPAS ----
st.subheader(f"🗺️ Mapas ({ano_sel})")

media_uf_ano = df_ano.groupby("SG_UF_ESC")["MEDIA"].mean().reset_index()

tab_estado, tab_mun = st.tabs(["Por Estado", "Por Município"])

with tab_estado:
    if geojson_estados is not None:
        fig = px.choropleth(
            media_uf_ano,
            geojson=geojson_estados,
            locations="SG_UF_ESC",
            featureidkey="properties.sigla",
            color="MEDIA",
            hover_name="SG_UF_ESC",
            color_continuous_scale="RdYlGn_r",
            title=f"Média geral por Estado — {ano_sel}",
        )
        fig.update_geos(fitbounds="locations", visible=True)
        fig.update_layout(margin=dict(l=0, r=0, t=40, b=0), height=500)
        st.plotly_chart(fig, use_container_width=True)


with tab_mun:
    if geojson_mun is not None and not comp.empty:
        rede_mapa = st.selectbox("🗺️ Rede para visualizar no mapa", comp["DEPENDENCIA"].unique())

        comp_rede = comp[comp["DEPENDENCIA"] == rede_mapa].dropna(subset=["GEOJSON_NAME"]).copy()
        qtd = st.slider("Top N municípios", 10, 300, 100, key="qtd_mun_mapa")
        top = comp_rede.nlargest(qtd, "MEDIA_MUN")

        metrica = st.radio("Métrica no mapa", ["MEDIA_MUN", "DIF_ESTADO", "DIF_NACIONAL"])
        labels = {
            "MEDIA_MUN": "Média do Município",
            "DIF_ESTADO": "Diferença vs Estado",
            "DIF_NACIONAL": "Diferença vs Brasil",
        }

        fig_mun = px.choropleth_mapbox(
            top,
            geojson=geojson_mun,
            locations="GEOJSON_NAME",
            featureidkey="properties.name",
            color=metrica,
            color_continuous_scale="RdYlGn_r" if metrica != "MEDIA_MUN" else "RdYlGn_r",
            mapbox_style="carto-positron",
            zoom=2.8,
            center={"lat": -14.2, "lon": -51.9},
            opacity=0.7,
            hover_data={
                "NO_MUNICIPIO_ESC": True,
                "SG_UF_ESC": True,
                "MEDIA_MUN": ":.2f",
                "MEDIA_EST": ":.2f",
                "MEDIA_NAC": ":.2f",
                "ESCOLAS_MUN": True,
            },
            title=f"{labels[metrica]} — Rede {rede_mapa} ({ano_sel})",
        )
        fig_mun.update_layout(margin=dict(l=0, r=0, t=40, b=0), height=600)
        st.plotly_chart(fig_mun, use_container_width=True)
    else:
        st.warning("GeoJSON não disponível ou dados vazios para o filtro selecionado.")

# ---- TABELA DE COMPARAÇÃO ----
st.subheader("📋 Tabela Comparativa por Município e Rede")

if not comp.empty:
    colunas = [
        "NO_MUNICIPIO_ESC", "SG_UF_ESC", "DEPENDENCIA",
        "MEDIA_MUN", "MEDIA_EST", "MEDIA_NAC",
        "DIF_ESTADO", "DIF_NACIONAL", "ESCOLAS_MUN",
    ]
    tab = comp[colunas].copy().sort_values(["DEPENDENCIA", "MEDIA_MUN"], ascending=[True, False])
    tab.columns = [
        "Município", "UF", "Rede",
        "Média Municipal", "Média Estadual", "Média Nacional",
        "Dif. vs Estado", "Dif. vs Brasil", "Escolas",
    ]
    st.dataframe(
        tab.style.format({
            "Média Municipal": "{:.2f}",
            "Média Estadual": "{:.2f}",
            "Média Nacional": "{:.2f}",
            "Dif. vs Estado": "{:+.2f}",
            "Dif. vs Brasil": "{:+.2f}",
        }),
        use_container_width=True,
        height=500,
    )

    csv = tab.to_csv(index=False, sep=";", decimal=",")
    st.download_button("Exportar CSV", data=csv, file_name=f"enem_municipio_rede_{ano_sel}.csv", mime="text/csv")

# ---- GRÁFICO DE BARRAS ----
st.subheader("📊 Comparação: Média Municipal vs Estadual vs Nacional")
if not comp.empty:
    rede_graf = st.selectbox("🏫 Rede", comp["DEPENDENCIA"].unique(), key="graf_rede")
    top_n = st.slider("Top N municípios", 5, 50, 20, key="top_graf")
    comp_graf = comp[comp["DEPENDENCIA"] == rede_graf].nlargest(top_n, "MEDIA_MUN")

    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        name="Municipal",
        x=comp_graf["NO_MUNICIPIO_ESC"] + " - " + comp_graf["SG_UF_ESC"],
        y=comp_graf["MEDIA_MUN"],
        marker_color="goldenrod",
    ))
    fig_bar.add_trace(go.Scatter(
        name="Estadual",
        x=comp_graf["NO_MUNICIPIO_ESC"] + " - " + comp_graf["SG_UF_ESC"],
        y=comp_graf["MEDIA_EST"],
        mode="lines+markers",
        line=dict(color="blue", width=3),
    ))
    fig_bar.add_trace(go.Scatter(
        name="Nacional",
        x=comp_graf["NO_MUNICIPIO_ESC"] + " - " + comp_graf["SG_UF_ESC"],
        y=comp_graf["MEDIA_NAC"],
        mode="lines+markers",
        line=dict(color="red", width=3, dash="dash"),
    ))
    fig_bar.update_layout(
        title=f"Top {top_n} municípios — Rede {rede_graf} ({ano_sel})",
        xaxis_tickangle=-45,
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

st.caption("Fonte: Dados do ENEM (INEP) — ranking por escola.")
