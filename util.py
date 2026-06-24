import unicodedata
import pandas as pd


def strip_accents(s: str) -> str:
    if not isinstance(s, str):
        return s
    nfkd = unicodedata.normalize("NFKD", s)
    return nfkd.encode("ASCII", "ignore").decode("ASCII")


def normalizar_cidade(nome: str) -> str:
    if not isinstance(nome, str):
        return nome
    return strip_accents(nome.strip().title())


def normalizar_dependencia(nome: str) -> str:
    if not isinstance(nome, str):
        return nome
    return nome.strip().title()


def normalizar_uf(sigla: str) -> str:
    if not isinstance(sigla, str):
        return sigla
    return sigla.strip().upper()


def normalizar_localizacao(nome: str) -> str:
    if not isinstance(nome, str):
        return nome
    return nome.strip().title()


def resolver_variantes(
    df: pd.DataFrame, col: str = "NO_MUNICIPIO_ESC"
) -> pd.Series:
    counts = df[col].value_counts()
    norm_to_canonical = {}
    for name in counts.index:
        key = strip_accents(name.strip().title())
        if key not in norm_to_canonical or counts[name] > counts.get(
            norm_to_canonical[key], 0
        ):
            norm_to_canonical[key] = name
    return df[col].apply(
        lambda x: norm_to_canonical.get(strip_accents(x.strip().title()), x)
    )


def normalizar_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if "DEPENDENCIA" in df.columns:
        df["DEPENDENCIA"] = df["DEPENDENCIA"].apply(normalizar_dependencia)
    if "SG_UF_ESC" in df.columns:
        df["SG_UF_ESC"] = df["SG_UF_ESC"].apply(normalizar_uf)
    if "NO_MUNICIPIO_ESC" in df.columns:
        df["NO_MUNICIPIO_ESC"] = resolver_variantes(df, "NO_MUNICIPIO_ESC")
    if "LOCALIZACAO" in df.columns and df["LOCALIZACAO"].dtype == "object":
        df["LOCALIZACAO"] = df["LOCALIZACAO"].apply(normalizar_localizacao)
    return df
