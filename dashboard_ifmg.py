import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from glob import glob
import re
from datetime import datetime

st.set_page_config(page_title="IFMG no ENEM 2014-2025", layout="wide", page_icon="")

st.markdown("""
<style>
    .title { font-size: 3rem; font-weight: 800; letter-spacing: -1px; margin-bottom: 0; }
    .subtitle { font-size: 1.1rem; color: #888; margin-top: 0; }
    .kpi-card { background: #0e1117; border: 1px solid #333; border-radius: 12px; padding: 1.2rem 1.5rem; text-align: center; }
    .kpi-value { font-size: 2rem; font-weight: 700; }
    .kpi-label { font-size: 0.8rem; color: #888; text-transform: uppercase; letter-spacing: 1px; }
    .kpi-delta { font-size: 0.9rem; }
    .insight-box { background: linear-gradient(135deg, #1a1a2e, #16213e); border-left: 4px solid #2ecc71; border-radius: 8px; padding: 1rem 1.5rem; margin: 1rem 0; }
    .insight-box h4 { color: #2ecc71; margin: 0 0 0.3rem 0; }
    .insight-box p { margin: 0; color: #ccc; }
    .ifmg-green { color: #2ecc71; font-weight: 700; }
    h2 { margin-top: 0.5rem; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────── DADOS ───────────────────────────

CAMPUS_CIDADES = [
    "Conselheiro Lafaiete", "Piumhi", "Ipatinga", "Itabirito", "Ponte Nova",
    "Formiga", "Bambuí", "Betim", "Ibirité", "Congonhas",
    "Governador Valadares", "Ouro Branco", "Ouro Preto",
    "Ribeirão Das Neves", "Sabará", "Santa Luzia", "São João Evangelista", "Arcos",
]

COR_CAMPUS = {
    "Conselheiro Lafaiete": "#e74c3c", "Piumhi": "#3498db", "Ipatinga": "#2ecc71",
    "Itabirito": "#f39c12", "Ponte Nova": "#9b59b6", "Formiga": "#1abc9c",
    "Bambuí": "#e67e22", "Betim": "#e74c3c", "Ibirité": "#3498db",
    "Congonhas": "#2ecc71", "Governador Valadares": "#f39c12", "Ouro Branco": "#9b59b6",
    "Ouro Preto": "#1abc9c", "Ribeirão Das Neves": "#e67e22", "Sabará": "#e74c3c",
    "Santa Luzia": "#3498db", "São João Evangelista": "#2ecc71", "Arcos": "#f39c12",
}

@st.cache_data(show_spinner="Carregando dados do ENEM...")
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
    df["DEPENDENCIA"] = df["DEPENDENCIA"].str.strip().str.title()
    df["SG_UF_ESC"] = df["SG_UF_ESC"].str.strip().str.upper()
    df["NO_MUNICIPIO_ESC"] = df["NO_MUNICIPIO_ESC"].str.strip().str.title()
    df["LOCALIZACAO"] = df["LOCALIZACAO"].str.strip().str.title() if df["LOCALIZACAO"].dtype == "object" else df["LOCALIZACAO"]
    return df


@st.cache_data
def preparar_dados_ifmg(df):
    df_ifmg = df[df["NO_MUNICIPIO_ESC"].isin(CAMPUS_CIDADES) & (df["SG_UF_ESC"] == "MG")].copy()
    df_ifmg["CAMPUS"] = df_ifmg["NO_MUNICIPIO_ESC"]
    return df_ifmg


with st.spinner("Carregando dados..."):
    df = carregar_dados()
    df_ifmg = preparar_dados_ifmg(df)

# Agregações base
nac = df.groupby("ANO").agg(MEDIA=("MEDIA", "mean")).reset_index()
nac.columns = ["ANO", "MEDIA_BR"]
nac["REDE"] = "Brasil"

nac_rede = df.groupby(["ANO", "DEPENDENCIA"]).agg(MEDIA=("MEDIA", "mean")).reset_index()
nac_rede.columns = ["ANO", "REDE", "MEDIA_BR"]

mg = df[df["SG_UF_ESC"] == "MG"].groupby(["ANO", "DEPENDENCIA"]).agg(MEDIA=("MEDIA", "mean")).reset_index()
mg.columns = ["ANO", "REDE", "MEDIA_MG"]

mg_fed = df[(df["SG_UF_ESC"] == "MG") & (df["DEPENDENCIA"] == "Federal")].groupby("ANO").agg(MEDIA=("MEDIA", "mean")).reset_index()
mg_fed.columns = ["ANO", "MEDIA_MG_FED"]

ifmg_campus = df_ifmg.groupby(["ANO", "CAMPUS", "DEPENDENCIA"]).agg(
    MEDIA=("MEDIA", "mean"), LC=("LC", "mean"), CH=("CH", "mean"),
    CN=("CN", "mean"), MT=("MT", "mean"), RD=("RD", "mean"),
    ESCOLAS=("MEDIA", "count"), ALUNOS=("ALUNOS", "sum"),
).reset_index().rename(columns={"DEPENDENCIA": "REDE"})

ifmg_geral = df_ifmg.groupby(["ANO", "DEPENDENCIA"]).agg(
    MEDIA=("MEDIA", "mean"), ESCOLAS=("MEDIA", "count"),
).reset_index()

# Montar tabela comparativa
comp = ifmg_campus.merge(mg, on=["ANO", "REDE"], how="left")
comp = comp.merge(nac_rede, on=["ANO", "REDE"], how="left")
comp["DIF_MG"] = comp["MEDIA"] - comp["MEDIA_MG"]
comp["DIF_BR"] = comp["MEDIA"] - comp["MEDIA_BR"]

# ─────────────────────────── HEADER ───────────────────────────

c_logo, c_titulo = st.columns([1, 5])
with c_logo:
    st.markdown("<h1 style='font-size:3rem; margin:0;'></h1>", unsafe_allow_html=True)
with c_titulo:
    st.markdown("<p class='title'>  IFMG no ENEM</p>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>A trajetória do Instituto Federal de Minas Gerais no ENEM 2014–2025 — desempenho, evolução e comparação com o Brasil</p>", unsafe_allow_html=True)

# KPIs
df_ifmg_fed = df_ifmg[df_ifmg["DEPENDENCIA"] == "Federal"]
media_ifmg_geral = df_ifmg_fed["MEDIA"].mean()
media_mg_federal = df[(df["SG_UF_ESC"] == "MG") & (df["DEPENDENCIA"] == "Federal")]["MEDIA"].mean()
media_br_federal = df[df["DEPENDENCIA"] == "Federal"]["MEDIA"].mean()
media_br_geral = df["MEDIA"].mean()
melhor_campus = df_ifmg_fed.groupby("CAMPUS")["MEDIA"].mean().idxmax()
total_reg = len(df_ifmg_fed)

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value ifmg-green">{media_ifmg_geral:.1f}</div>
        <div class="kpi-label">Média IFMG (Rede Federal)</div>
    </div>""", unsafe_allow_html=True)
with k2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value" style="color:#3498db">{media_mg_federal:.1f}</div>
        <div class="kpi-label">Média MG (Rede Federal)</div>
    </div>""", unsafe_allow_html=True)
with k3:
    diff = media_ifmg_geral - media_br_federal
    cor = "#2ecc71" if diff > 0 else "#e74c3c"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value" style="color:{cor}">{diff:+.1f}</div>
        <div class="kpi-label">IFMG vs Brasil Federal</div>
    </div>""", unsafe_allow_html=True)
with k4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value" style="color:#f39c12">=>{melhor_campus}</div>
        <div class="kpi-label">Maior média</div>
    </div>""", unsafe_allow_html=True)
with k5:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value">{total_reg:,}</div>
        <div class="kpi-label">Registros IFMG (Federal)</div>
    </div>""", unsafe_allow_html=True)

st.markdown("---")

# ─────────────────────────── CAPÍTULO 1: PANORAMA IFMG ───────────────────────────

st.markdown("##   Capítulo 1: O IFMG no Contexto Nacional")
st.markdown("Como o IFMG se posiciona frente ao Brasil e ao estado de Minas Gerais?")

c1, c2 = st.columns([2, 1])

with c1:
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=nac["ANO"], y=nac["MEDIA_BR"], mode="lines+markers",
        name="Brasil (todas as redes)", line=dict(color="#888", width=2, dash="dash"),
        marker=dict(size=6), hovertemplate="%{x}: %{y:.1f}<extra></extra>",
    ))
    fig1.add_trace(go.Scatter(
        x=nac[nac_rede["REDE"] == "Federal"]["ANO"],
        y=nac_rede[nac_rede["REDE"] == "Federal"]["MEDIA_BR"],
        mode="lines+markers", name="Brasil (Rede Federal)",
        line=dict(color="#e74c3c", width=2, dash="dot"), marker=dict(size=6),
    ))
    fig1.add_trace(go.Scatter(
        x=mg_fed["ANO"], y=mg_fed["MEDIA_MG_FED"],
        mode="lines+markers", name="MG (Rede Federal)",
        line=dict(color="#3498db", width=3), marker=dict(size=8),
    ))
    fig1.add_trace(go.Scatter(
        x=ifmg_geral[ifmg_geral["DEPENDENCIA"] == "Federal"]["ANO"],
        y=ifmg_geral[ifmg_geral["DEPENDENCIA"] == "Federal"]["MEDIA"],
        mode="lines+markers", name="IFMG (todos os campi)",
        line=dict(color="#2ecc71", width=4), marker=dict(size=10),
    ))
    fig1.update_layout(title="Evolução da Média: IFMG vs Brasil vs MG (Rede Federal)", height=450,
                       hovermode="x unified", xaxis=dict(dtick=1),
                       margin=dict(l=0, r=0, t=50, b=0))
    st.plotly_chart(fig1, use_container_width=True)

with c2:
    st.markdown('<div class="insight-box">', unsafe_allow_html=True)
    st.markdown("**  IFMG acima da média**")
    diff_ifmg_br = media_ifmg_geral - media_br_federal
    diff_ifmg_mg = media_ifmg_geral - media_mg_federal
    st.markdown(f"""
    O IFMG supera a média da rede federal brasileira em **{diff_ifmg_br:.1f} pontos** 
    e a média mineira da rede federal em **{diff_ifmg_mg:.1f} pontos**.
    """)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="insight-box">', unsafe_allow_html=True)
    st.markdown("**  Crescimento consistente**")
    fed_evol = ifmg_geral[ifmg_geral["DEPENDENCIA"] == "Federal"].set_index("ANO")["MEDIA"]
    ano_ini = int(fed_evol.first_valid_index())
    ano_fim = int(fed_evol.last_valid_index())
    med_ini = fed_evol.loc[ano_ini]
    med_fim = fed_evol.loc[ano_fim]
    st.markdown(f"""
    A média dos campi IFMG subiu de **{med_ini:.0f}** ({ano_ini}) 
    para **{med_fim:.0f}** ({ano_fim}) — 
    um crescimento de **{med_fim - med_ini:.0f} pontos**.
    """)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")

# ─────────────────────────── CAPÍTULO 2: RANKING DOS CAMPI ───────────────────────────

st.markdown("##   Capítulo 2: O Ranking dos Campi")
st.markdown("Qual campus lidera? Qual mais evoluiu? Como se comparam entre si?")

c3, c4 = st.columns(2)

with c3:
    rank_campus = df_ifmg[df_ifmg["DEPENDENCIA"] == "Federal"].groupby("CAMPUS")["MEDIA"].mean().sort_values(ascending=False).reset_index()
    rank_campus.columns = ["CAMPUS", "MEDIA"]
    rank_campus["COR"] = rank_campus["CAMPUS"].map(COR_CAMPUS)

    fig_rank = px.bar(rank_campus, x="MEDIA", y="CAMPUS", orientation="h",
                      color="MEDIA", color_continuous_scale="Greens",
                      text=rank_campus["MEDIA"].round(1).astype(str),
                      title="Ranking dos Campi IFMG (média geral 2014-2025)")
    fig_rank.update_layout(height=500, yaxis=dict(categoryorder="total ascending"),
                           showlegend=False, margin=dict(l=0, r=0, t=50, b=0))
    fig_rank.update_traces(textposition="outside")
    st.plotly_chart(fig_rank, use_container_width=True)

with c4:
    st.markdown("###   Série Temporal por Campus")
    campus_sel = st.selectbox("Selecione um campus", CAMPUS_CIDADES, key="campus_ts")
    df_c = df_ifmg[(df_ifmg["CAMPUS"] == campus_sel) & (df_ifmg["DEPENDENCIA"] == "Federal")].sort_values("ANO")
    df_c_br = nac_rede[nac_rede["REDE"] == "Federal"].copy()
    df_c_mg = mg[mg["REDE"] == "Federal"].copy()

    fig_ts = go.Figure()
    fig_ts.add_trace(go.Scatter(x=df_c["ANO"], y=df_c["MEDIA"], mode="lines+markers",
                                name=campus_sel, line=dict(color=COR_CAMPUS.get(campus_sel, "#2ecc71"), width=4),
                                marker=dict(size=10), hovertemplate="%{x}: %{y:.1f}<extra></extra>"))
    fig_ts.add_trace(go.Scatter(x=df_c_br["ANO"], y=df_c_br["MEDIA_BR"], mode="lines",
                                name="Brasil (Federal)", line=dict(color="#e74c3c", width=2, dash="dash")))
    fig_ts.add_trace(go.Scatter(x=df_c_mg["ANO"], y=df_c_mg["MEDIA_MG"], mode="lines",
                                name="MG (Federal)", line=dict(color="#3498db", width=2, dash="dot")))
    fig_ts.update_layout(title=f"{campus_sel} vs Brasil e MG (Rede Federal)", height=400,
                         hovermode="x unified", xaxis=dict(dtick=1),
                         margin=dict(l=0, r=0, t=50, b=0))
    st.plotly_chart(fig_ts, use_container_width=True)

# ─── Gap: IFMG vs BR/MG ───
st.markdown("###   Diferença em relação ao Brasil e MG (por campus)")

comp_fed = comp[comp["REDE"] == "Federal"].groupby("CAMPUS")[["MEDIA", "MEDIA_BR", "MEDIA_MG"]].mean().reset_index()
comp_fed["DIF_BR"] = comp_fed["MEDIA"] - comp_fed["MEDIA_BR"]
comp_fed["DIF_MG"] = comp_fed["MEDIA"] - comp_fed["MEDIA_MG"]
comp_fed = comp_fed.sort_values("DIF_BR", ascending=False)

fig_gap = go.Figure()
fig_gap.add_trace(go.Bar(
    name="vs Brasil (Federal)", x=comp_fed["CAMPUS"], y=comp_fed["DIF_BR"],
    marker_color="#2ecc71", hovertemplate="%{x}: %{y:+.1f}<extra></extra>",
))
fig_gap.add_trace(go.Bar(
    name="vs MG (Federal)", x=comp_fed["CAMPUS"], y=comp_fed["DIF_MG"],
    marker_color="#3498db", hovertemplate="%{x}: %{y:+.1f}<extra></extra>",
))
fig_gap.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.3)
fig_gap.update_layout(title="Quanto cada campus supera (ou fica abaixo) da média", height=400,
                      barmode="group", xaxis_tickangle=-45,
                      margin=dict(l=0, r=0, t=50, b=0))
st.plotly_chart(fig_gap, use_container_width=True)

st.markdown("---")

# ─────────────────────────── CAPÍTULO 3: EVOLUÇÃO DOS CAMPI ───────────────────────────

st.markdown("##   Capítulo 3: Quem Mais Evoluiu?")
st.markdown("A trajetória individual de cada campus ao longo da década.")

c5, c6 = st.columns(2)

with c5:
    evol_data = df_ifmg[df_ifmg["DEPENDENCIA"] == "Federal"].groupby(["CAMPUS", "ANO"]).agg(
        MEDIA=("MEDIA", "mean"), ALUNOS=("ALUNOS", "sum")
    ).reset_index()
    evol_data = evol_data[evol_data["ALUNOS"] >= 10]

    evol_campus_list = []
    for campus, grp in evol_data.groupby("CAMPUS"):
        grp = grp.sort_values("ANO")
        if len(grp) >= 2:
            first = grp.iloc[0]
            last = grp.iloc[-1]
            evol_campus_list.append({
                "CAMPUS": campus,
                "PRIMEIRO_ANO": int(first["ANO"]),
                "ULTIMO_ANO": int(last["ANO"]),
                "MEDIA_INI": first["MEDIA"],
                "MEDIA_FIM": last["MEDIA"],
                "EVOLUCAO": last["MEDIA"] - first["MEDIA"],
            })

    evol_campus = pd.DataFrame(evol_campus_list).sort_values("EVOLUCAO", ascending=False)
    if not evol_campus.empty:
        evol_campus["ROTULO"] = evol_campus.apply(
            lambda r: f"{r['EVOLUCAO']:.1f} ({r['PRIMEIRO_ANO']}→{r['ULTIMO_ANO']})", axis=1
        )
        fig_evol = px.bar(evol_campus.head(10), x="EVOLUCAO", y="CAMPUS", orientation="h",
                          color="EVOLUCAO", color_continuous_scale="Greens",
                          text=evol_campus.head(10)["ROTULO"],
                          title="Maior Evolução (primeiro → último ano disponível)")
        fig_evol.update_layout(height=400, yaxis=dict(categoryorder="total ascending"),
                               showlegend=False, margin=dict(l=0, r=0, t=50, b=0))
        fig_evol.update_traces(textposition="outside")
        st.plotly_chart(fig_evol, use_container_width=True)

with c6:
    if not evol_campus.empty:
        estagnados = evol_campus.sort_values("EVOLUCAO").head(10)
        fig_est = px.bar(estagnados, x="EVOLUCAO", y="CAMPUS", orientation="h",
                         color="EVOLUCAO", color_continuous_scale="Reds_r",
                         text=estagnados["ROTULO"],
                         title="Menor Evolução (primeiro → último ano disponível)")
        fig_est.update_layout(height=400, yaxis=dict(categoryorder="total ascending"),
                              showlegend=False, margin=dict(l=0, r=0, t=50, b=0))
        fig_est.update_traces(textposition="outside")
        st.plotly_chart(fig_est, use_container_width=True)

# Bump chart dos campi
st.markdown("###   Corrida dos Campi: Ranking Ano a Ano")

rank_ano = df_ifmg[df_ifmg["DEPENDENCIA"] == "Federal"].groupby(["ANO", "CAMPUS"])["MEDIA"].mean().reset_index()
rank_ano["RANK"] = rank_ano.groupby("ANO")["MEDIA"].rank(ascending=False)

fig_bump = go.Figure()
for camp in sorted(rank_ano["CAMPUS"].unique()):
    d = rank_ano[rank_ano["CAMPUS"] == camp].sort_values("ANO")
    fig_bump.add_trace(go.Scatter(
        x=d["ANO"], y=d["RANK"], mode="lines+markers", name=camp,
        line=dict(width=3, color=COR_CAMPUS.get(camp, "#888")),
        marker=dict(size=8), text=d["RANK"].astype(int), textposition="middle right",
        hovertemplate="%{x}: %{y:.0f}º<extra></extra>",
    ))
fig_bump.update_layout(title="Posição no Ranking Interno do IFMG", height=450,
                       yaxis=dict(autorange="reversed", dtick=1, title="Posição"),
                       xaxis=dict(dtick=1), hovermode="x unified",
                       margin=dict(l=0, r=0, t=50, b=0))
st.plotly_chart(fig_bump, use_container_width=True)

st.markdown("---")

# ─────────────────────────── CAPÍTULO 4: PERFIL POR DISCIPLINA ───────────────────────────

st.markdown("##   Capítulo 4: O Perfil de Cada Campus")
st.markdown("Em qual disciplina cada campus se destaca? Como é o perfil do IFMG?")

disciplinas = ["LC", "CH", "CN", "MT", "RD"]
labels_disc = {"LC": "Linguagens", "CH": "Humanas", "CN": "Natureza", "MT": "Matemática", "RD": "Redação"}

c7, c8 = st.columns([1.5, 1])

with c7:
    radar_data = df_ifmg[df_ifmg["DEPENDENCIA"] == "Federal"].groupby("CAMPUS")[disciplinas].mean().reset_index()
    fig_radar = go.Figure()
    for _, row in radar_data.iterrows():
        vals = row[disciplinas].tolist() + [row[disciplinas].tolist()[0]]
        theta = [labels_disc[d] for d in disciplinas] + [labels_disc[disciplinas[0]]]
        fig_radar.add_trace(go.Scatterpolar(
            r=vals, theta=theta, name=row["CAMPUS"],
            line=dict(width=2, color=COR_CAMPUS.get(row["CAMPUS"], "#888")),
            opacity=0.7,
        ))
    fig_radar.update_layout(title="Perfil por Disciplina — Todos os Campi", height=500,
                            polar=dict(radialaxis=dict(visible=True, range=[450, 750])),
                            margin=dict(l=80, r=80, t=50, b=0))
    st.plotly_chart(fig_radar, use_container_width=True)

with c8:
    campus_radar = st.selectbox("Campus para destaque", CAMPUS_CIDADES, key="campus_radar")
    df_cr = radar_data[radar_data["CAMPUS"] == campus_radar]
    if not df_cr.empty:
        vals = df_cr[disciplinas].iloc[0].tolist()
        theta = [labels_disc[d] for d in disciplinas]

        fig_single = go.Figure()
        fig_single.add_trace(go.Scatterpolar(
            r=vals + [vals[0]], theta=theta + [theta[0]],
            name=campus_radar, fill="toself",
            line=dict(width=3, color=COR_CAMPUS.get(campus_radar, "#2ecc71")),
        ))
        fig_single.update_layout(title=campus_radar, height=400,
                                 polar=dict(radialaxis=dict(visible=True, range=[450, 750])),
                                 margin=dict(l=80, r=80, t=50, b=0))
        st.plotly_chart(fig_single, use_container_width=True)

    st.markdown('<div class="insight-box">', unsafe_allow_html=True)
    melhor_disc = df_cr[disciplinas].iloc[0].idxmax() if not df_cr.empty else ""
    melhor_disc_nome = labels_disc.get(melhor_disc, "")
    pior_disc = df_cr[disciplinas].iloc[0].idxmin() if not df_cr.empty else ""
    pior_disc_nome = labels_disc.get(pior_disc, "")
    if melhor_disc_nome:
        st.markdown(f"**  Destaque**")
        st.markdown(f"""
        {campus_radar} tem seu melhor desempenho em **{melhor_disc_nome}** 
        e maior desafio em **{pior_disc_nome}**.
        """)
    st.markdown("</div>", unsafe_allow_html=True)

# ─── Dispersão ───
st.markdown("###   Matemática vs Redação: O Diferencial IFMG")

ano_disp = st.selectbox("Ano", sorted(df["ANO"].unique()), key="ano_disp_ifmg")
df_disp = df_ifmg[(df_ifmg["ANO"] == ano_disp) & (df_ifmg["DEPENDENCIA"] == "Federal")].groupby(
    "CAMPUS"
).agg(MT=("MT", "mean"), RD=("RD", "mean"), MEDIA=("MEDIA", "mean"), ESCOLAS=("MEDIA", "count")).reset_index()

fig_disp = px.scatter(
    df_disp, x="MT", y="RD", text="CAMPUS", size="ESCOLAS",
    color="MEDIA", color_continuous_scale="RdYlGn",
    title=f"Matemática × Redação por Campus — {ano_disp}",
    labels={"MT": "Matemática (média)", "RD": "Redação (média)", "MEDIA": "Média Geral"},
    size_max=25,
)
fig_disp.update_traces(textposition="top center", marker=dict(line=dict(width=1, color="white")))
fig_disp.add_hline(y=df_disp["RD"].mean(), line_dash="dash", line_color="gray", opacity=0.4)
fig_disp.add_vline(x=df_disp["MT"].mean(), line_dash="dash", line_color="gray", opacity=0.4)
fig_disp.update_layout(height=500, margin=dict(l=0, r=0, t=50, b=0))
st.plotly_chart(fig_disp, use_container_width=True)

st.markdown("---")

# ─────────────────────────── CAPÍTULO 5: IFMG vs REDES LOCAIS ───────────────────────────

st.markdown("##   Capítulo 5: IFMG vs as Demais Redes nos Mesmos Municípios")
st.markdown("Como o IFMG (Federal) se compara com as redes Estadual, Municipal e Privada nas mesmas cidades?")

campus_comp = st.selectbox("Campus", CAMPUS_CIDADES, key="campus_comp")
df_cc = df_ifmg[df_ifmg["CAMPUS"] == campus_comp].groupby(["ANO", "DEPENDENCIA"])["MEDIA"].mean().reset_index()

fig_comp = go.Figure()
cores_comp = {"Federal": "#2ecc71", "Estadual": "#e74c3c", "Municipal": "#f39c12", "Privada": "#3498db"}
for rede in df_cc["DEPENDENCIA"].unique():
    d = df_cc[df_cc["DEPENDENCIA"] == rede].sort_values("ANO")
    fig_comp.add_trace(go.Scatter(
        x=d["ANO"], y=d["MEDIA"], mode="lines+markers",
        name=rede, line=dict(width=3, color=cores_comp.get(rede, "#888")),
        marker=dict(size=8),
    ))
fig_comp.add_trace(go.Scatter(
    x=nac_rede[nac_rede["REDE"] == "Federal"]["ANO"],
    y=nac_rede[nac_rede["REDE"] == "Federal"]["MEDIA_BR"],
    mode="lines", name="Brasil (Federal)", line=dict(color="#888", width=2, dash="dash"),
))
fig_comp.update_layout(title=f"Comparação entre Redes — {campus_comp}", height=450,
                       hovermode="x unified", xaxis=dict(dtick=1),
                       margin=dict(l=0, r=0, t=50, b=0))
st.plotly_chart(fig_comp, use_container_width=True)

# Heatmap: todos campus x redes
st.markdown("###   Matriz: Média por Campus e Rede (todos os anos)")

matriz = df_ifmg.groupby(["CAMPUS", "DEPENDENCIA"])["MEDIA"].mean().reset_index()
heat = matriz.pivot(index="CAMPUS", columns="DEPENDENCIA", values="MEDIA")
fig_heat = px.imshow(heat, text_auto=".0f", aspect="auto",
                     color_continuous_scale="RdYlGn",
                     title="Média por Campus e Rede de Ensino",
                     labels=dict(x="Rede", y="Campus", color="Média"))
fig_heat.update_layout(height=500, margin=dict(l=0, r=0, t=50, b=0))
st.plotly_chart(fig_heat, use_container_width=True)

st.markdown("---")

# ─────────────────────────── CAPÍTULO 6: TABELA COMPARATIVA ───────────────────────────

st.markdown("##   Capítulo 6: Tabela Comparativa")
st.markdown("Todos os dados em uma tabela para análise detalhada.")

ano_tab = st.selectbox("Ano", sorted(df["ANO"].unique()), key="ano_tab_ifmg")
rede_tab = st.selectbox("Rede", ["Federal", "Estadual", "Municipal", "Privada"], key="rede_tab_ifmg")

tab_filtro = comp[(comp["ANO"] == ano_tab) & (comp["REDE"] == rede_tab)].copy()
tab_filtro = tab_filtro.sort_values("MEDIA", ascending=False)

if not tab_filtro.empty:
    tab_show = tab_filtro[["CAMPUS", "MEDIA", "MEDIA_MG", "MEDIA_BR", "DIF_MG", "DIF_BR", "LC", "CH", "CN", "MT", "RD", "ESCOLAS"]].reset_index(drop=True)
    tab_show.columns = ["Campus", "Média", "Média MG", "Média Brasil", "Dif. vs MG", "Dif. vs BR",
                        "LC", "CH", "CN", "MT", "RD", "Escolas"]
    st.dataframe(
        tab_show.style.format({
            "Média": "{:.2f}", "Média MG": "{:.2f}", "Média Brasil": "{:.2f}",
            "Dif. vs MG": "{:+.2f}", "Dif. vs BR": "{:+.2f}",
            "LC": "{:.1f}", "CH": "{:.1f}", "CN": "{:.1f}", "MT": "{:.1f}", "RD": "{:.1f}",
        }),
        use_container_width=True, height=400,
    )

    csv = tab_show.to_csv(index=False, sep=";", decimal=",")
    st.download_button("Exportar CSV", data=csv, file_name=f"ifmg_{ano_tab}_{rede_tab}.csv", mime="text/csv")

st.markdown("---")
st.markdown(f"""
<div style="text-align:center; color:#666; font-size:0.85rem; padding:1rem;">
    Dashboard IFMG no ENEM — Dados ENEM/INEP (2014–2025) | {datetime.now().strftime('%B %Y')}<br>
    {len(CAMPUS_CIDADES)} campi analisados em {len(df_ifmg_fed):,} registros ao longo de 12 anos.
    https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem.<br>
    Desenvolvido por luciano.espiriao@ifmg.edu.br. 2026 - Todos os direitos reservados.    
</div>
""", unsafe_allow_html=True)
