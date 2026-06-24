import streamlit as st
import pandas as pd
from glob import glob
import re
import util


@st.cache_data(show_spinner="Carregando 12 anos de ENEM...")
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
    for col in ["LC", "CH", "CN", "MT", "RD", "MEDIA"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = util.normalizar_dataframe(df)
    regioes = {
        "AC": "Norte", "AP": "Norte", "AM": "Norte", "PA": "Norte", "RO": "Norte", "RR": "Norte", "TO": "Norte",
        "AL": "Nordeste", "BA": "Nordeste", "CE": "Nordeste", "MA": "Nordeste", "PB": "Nordeste",
        "PE": "Nordeste", "PI": "Nordeste", "RN": "Nordeste", "SE": "Nordeste",
        "DF": "Centro-Oeste", "GO": "Centro-Oeste", "MT": "Centro-Oeste", "MS": "Centro-Oeste",
        "ES": "Sudeste", "MG": "Sudeste", "RJ": "Sudeste", "SP": "Sudeste",
        "PR": "Sul", "RS": "Sul", "SC": "Sul",
    }
    df["REGIAO"] = df["SG_UF_ESC"].map(regioes)
    return df


@st.cache_data(show_spinner="Carregando mapa de Institutos Federais...")
def carregar_campi_if():
    campi = pd.read_csv("dados/campi_institutos_federais.csv", sep=",")
    campi.columns = campi.columns.str.strip()
    campi["municipio_norm"] = campi["municipio"].apply(util.normalizar_cidade)
    campi["uf"] = campi["uf"].str.strip().str.upper()
    return campi


@st.cache_data(show_spinner="Carregando Rede Federal completa...")
def carregar_rede_federal():
    campi = pd.read_csv("dados/campi_rede_federal.csv", sep=",")
    campi.columns = campi.columns.str.strip()
    campi["municipio_norm"] = campi["municipio"].apply(util.normalizar_cidade)
    campi["uf"] = campi["uf"].str.strip().str.upper()
    campi["tipo_instituicao"] = campi["tipo_instituicao"].str.strip().str.upper()
    return campi


@st.cache_data
def preparar_dados_if(df, campi):
    campi_norm = campi[["municipio_norm", "uf", "instituto_federal"]].drop_duplicates()
    df = df.copy()
    df["_merge_norm"] = df["NO_MUNICIPIO_ESC"].apply(util.normalizar_cidade)
    df_if = df.merge(
        campi_norm,
        left_on=["_merge_norm", "SG_UF_ESC"],
        right_on=["municipio_norm", "uf"],
        how="inner",
    ).drop(columns=["_merge_norm", "municipio_norm"]).copy()
    df_if["INSTITUTO"] = df_if["instituto_federal"]
    df_if["CAMPUS"] = df_if["NO_MUNICIPIO_ESC"]
    return df_if


@st.cache_data
def preparar_dados_rede_federal(df, campi_rede):
    campi = campi_rede.copy()
    # Usa municipio_merge quando disponível (ex: CPII), senão usa municipio
    campi["merge_key"] = campi["municipio_merge"].where(
        campi["municipio_merge"].notna() & (campi["municipio_merge"] != ""),
        campi["municipio"]
    )
    campi["merge_norm"] = campi["merge_key"].apply(util.normalizar_cidade)
    campi_norm = campi[["merge_norm", "uf", "instituicao", "tipo_instituicao"]].drop_duplicates()
    df = df.copy()
    df["_merge_norm"] = df["NO_MUNICIPIO_ESC"].apply(util.normalizar_cidade)
    df_rede = df.merge(
        campi_norm,
        left_on=["_merge_norm", "SG_UF_ESC"],
        right_on=["merge_norm", "uf"],
        how="inner",
    ).drop(columns=["_merge_norm", "merge_norm"]).copy()
    df_rede["INSTITUICAO"] = df_rede["instituicao"]
    df_rede["TIPO_INSTITUICAO"] = df_rede["tipo_instituicao"]
    df_rede["CAMPUS"] = df_rede["NO_MUNICIPIO_ESC"]
    return df_rede


@st.cache_data
def preparar_agregacoes(df):
    nac = df.groupby("ANO").agg(MEDIA=("MEDIA", "mean"), ESCOLAS=("MEDIA", "count"), ALUNOS_TOTAL=("ALUNOS", "sum")).reset_index()
    nac["REDE"] = "Brasil"

    nac_rede = df.groupby(["ANO", "DEPENDENCIA"]).agg(MEDIA=("MEDIA", "mean"), ESCOLAS=("MEDIA", "count")).reset_index()
    nac_rede.rename(columns={"DEPENDENCIA": "REDE"}, inplace=True)

    regiao = df.groupby(["ANO", "REGIAO"]).agg(MEDIA=("MEDIA", "mean")).reset_index()

    uf = df.groupby(["ANO", "SG_UF_ESC"]).agg(MEDIA=("MEDIA", "mean")).reset_index()

    rede_ano = df.groupby(["ANO", "DEPENDENCIA"]).agg(
        MEDIA=("MEDIA", "mean"), LC=("LC", "mean"), CH=("CH", "mean"),
        CN=("CN", "mean"), MT=("MT", "mean"), RD=("RD", "mean"),
    ).reset_index()

    return nac, nac_rede, regiao, uf, rede_ano


@st.cache_data
def preparar_tabela_completa(df):
    return df.groupby(["ANO", "REGIAO", "SG_UF_ESC", "NO_MUNICIPIO_ESC", "DEPENDENCIA", "LOCALIZACAO"]).agg(
        MEDIA=("MEDIA", "mean"), LC=("LC", "mean"), CH=("CH", "mean"),
        CN=("CN", "mean"), MT=("MT", "mean"), RD=("RD", "mean"),
        ESCOLAS=("MEDIA", "count"), ALUNOS=("ALUNOS", "sum"),
    ).reset_index()
