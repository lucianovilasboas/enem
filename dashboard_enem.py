import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from glob import glob
import re
from datetime import datetime

st.set_page_config(page_title="ENEM 2014-2025 — História em Dados", layout="wide", page_icon="")

st.markdown("""
<style>
    .title { font-size: 3rem; font-weight: 800; letter-spacing: -1px; margin-bottom: 0; }
    .subtitle { font-size: 1.1rem; color: #888; margin-top: 0; }
    .kpi-card { background: #0e1117; border: 1px solid #333; border-radius: 12px; padding: 1.2rem 1.5rem; text-align: center; }
    .kpi-value { font-size: 2.2rem; font-weight: 700; }
    .kpi-label { font-size: 0.8rem; color: #888; text-transform: uppercase; letter-spacing: 1px; }
    .kpi-delta { font-size: 0.9rem; }
    .insight-box { background: linear-gradient(135deg, #1a1a2e, #16213e); border-left: 4px solid #e94560; border-radius: 8px; padding: 1rem 1.5rem; margin: 1rem 0; }
    .insight-box h4 { color: #e94560; margin: 0 0 0.3rem 0; }
    .insight-box p { margin: 0; color: #ccc; }
    h2 { margin-top: 0.5rem; }
    .stButton > button { border-radius: 20px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────── DADOS ───────────────────────────

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
    df["DEPENDENCIA"] = df["DEPENDENCIA"].str.strip().str.title()
    df["SG_UF_ESC"] = df["SG_UF_ESC"].str.strip().str.upper()
    df["NO_MUNICIPIO_ESC"] = df["NO_MUNICIPIO_ESC"].str.strip().str.title()
    df["LOCALIZACAO"] = df["LOCALIZACAO"].str.strip().str.title() if df["LOCALIZACAO"].dtype == "object" else df["LOCALIZACAO"]

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


@st.cache_data
def preparar_agregacoes(df):
    nac = df.groupby("ANO").agg(MEDIA=("MEDIA", "mean"), ESCOLAS=("MEDIA", "count"), ALUNOS_TOTAL=("ALUNOS", "sum")).reset_index()
    nac["REDE"] = "Brasil"

    nac_rede = df.groupby(["ANO", "DEPENDENCIA"]).agg(MEDIA=("MEDIA", "mean"), ESCOLAS=("MEDIA", "count")).reset_index()
    nac_rede.rename(columns={"DEPENDENCIA": "REDE"}, inplace=True)

    regiao = df.groupby(["ANO", "REGIAO"]).agg(MEDIA=("MEDIA", "mean")).reset_index()

    regiao_rede = df.groupby(["ANO", "REGIAO", "DEPENDENCIA"]).agg(MEDIA=("MEDIA", "mean")).reset_index()
    regiao_rede.rename(columns={"DEPENDENCIA": "REDE"}, inplace=True)

    uf = df.groupby(["ANO", "SG_UF_ESC"]).agg(MEDIA=("MEDIA", "mean")).reset_index()

    rede_ano = df.groupby(["ANO", "DEPENDENCIA"]).agg(
        MEDIA=("MEDIA", "mean"), LC=("LC", "mean"), CH=("CH", "mean"),
        CN=("CN", "mean"), MT=("MT", "mean"), RD=("RD", "mean"),
    ).reset_index()

    return nac, nac_rede, regiao, regiao_rede, uf, rede_ano


@st.cache_data
def preparar_tabela_completa(df):
    return df.groupby(["ANO", "REGIAO", "SG_UF_ESC", "NO_MUNICIPIO_ESC", "DEPENDENCIA", "LOCALIZACAO"]).agg(
        MEDIA=("MEDIA", "mean"), LC=("LC", "mean"), CH=("CH", "mean"),
        CN=("CN", "mean"), MT=("MT", "mean"), RD=("RD", "mean"),
        ESCOLAS=("MEDIA", "count"), ALUNOS=("ALUNOS", "sum"),
    ).reset_index()


with st.spinner("Carregando dados..."):
    df = carregar_dados()
    nac, nac_rede, regiao, regiao_rede, uf, rede_ano = preparar_agregacoes(df)
    tab_completa = preparar_tabela_completa(df)

# ─────────────────────────── KPI GLOBAIS ───────────────────────────

media_geral = nac["MEDIA"].mean()
nac_idx = nac.set_index("ANO")["MEDIA"]
gap_2014_2025 = nac_idx.loc[2025] - nac_idx.loc[2014]
gap_rede = df.groupby("DEPENDENCIA")["MEDIA"].mean()
gap_priv_pub = gap_rede["Privada"] - gap_rede["Estadual"]

# ─────────────────────────── HEADER ───────────────────────────

st.markdown('<p class="title">  ENEM 2014–2025</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Uma década de educação brasileira em dados — tendências, desigualdades e surpresas</p>', unsafe_allow_html=True)

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value">{media_geral:.1f}</div>
        <div class="kpi-label">Média Anual Nacional</div>
    </div>
    """, unsafe_allow_html=True)
with k2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value" style="color:#4ecdc4">+{gap_2014_2025:.1f}</div>
        <div class="kpi-label">Evolução 2014→2025</div>
    </div>
    """, unsafe_allow_html=True)
with k3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value" style="color:#e94560">{gap_priv_pub:.0f}</div>
        <div class="kpi-label">Gap Privada vs Pública</div>
    </div>
    """, unsafe_allow_html=True)
with k4:
    top_rede = gap_rede.idxmax()
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value" style="color:#ffd93d">{gap_rede.max():.1f}</div>
        <div class="kpi-label">Melhor Rede: {top_rede}</div>
    </div>
    """, unsafe_allow_html=True)
with k5:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value">{len(df):,}</div>
        <div class="kpi-label">Escolas-rankings analisados</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ─────────────────────────── CAPÍTULO 1: VISÃO GERAL ───────────────────────────

st.markdown("##   Capítulo 1: A Década do ENEM")
st.markdown("Como evoluiu a média nacional ao longo de 12 anos? Quem foram os protagonistas?")

c1, c2 = st.columns([2, 1])

with c1:
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=nac["ANO"], y=nac["MEDIA"], mode="lines+markers+text",
        line=dict(color="#4ecdc4", width=4), marker=dict(size=10, color="#4ecdc4"),
        text=nac["MEDIA"].round(1), textposition="top center",
        name="Brasil", hovertemplate="%{x}: %{y:.1f}<extra></extra>",
    ))
    med_por_ano = nac.set_index("ANO")["MEDIA"]
    for a in [2014, 2020, 2022, 2025]:
        if a in med_por_ano.index:
            y_val = med_por_ano.loc[a]
            fig1.add_annotation(x=a, y=y_val, text=f"<b>{y_val:.1f}</b>",
                                showarrow=True, arrowhead=3, arrowsize=1.5, ax=0, ay=-40, font=dict(size=13))
    fig1.update_layout(title="Evolução da Média Nacional no ENEM", height=450,
                       xaxis=dict(dtick=1, tickangle=0), hovermode="x unified",
                       yaxis=dict(range=[480, 540]), margin=dict(l=0, r=0, t=50, b=0))
    st.plotly_chart(fig1, use_container_width=True)

with c2:
    st.markdown('<div class="insight-box">', unsafe_allow_html=True)
    st.markdown("**   Tendência de alta**")
    nac["DIF"] = nac["MEDIA"].diff()
    max_jump = nac.loc[nac["DIF"].idxmax()]
    st.markdown(f"""
    A média nacional subiu **{gap_2014_2025:+.1f} pontos** em 12 anos — um crescimento consistente, 
    com aceleração notável a partir de 2022. O maior salto foi entre {int(max_jump['ANO'])-1} e {int(max_jump['ANO'])} (+{max_jump['DIF']:.1f} pts).
    """)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="insight-box">', unsafe_allow_html=True)
    st.markdown("**  Pandemia e recuperação**")
    st.markdown("""
    2020 e 2021 (pandemia) mostraram estabilidade, não queda — surpreendente. 
    A recuperação veio forte em 2022, possivelmente refletindo adaptação ao ensino remoto.
    """)
    st.markdown("</div>", unsafe_allow_html=True)

# ─── Gráfico de Redes ───
st.markdown("###  Abertura por Rede de Ensino")

c3, c4 = st.columns([2, 1])

with c3:
    cores_rede = {"Federal": "#e94560", "Estadual": "#4ecdc4", "Municipal": "#ffd93d", "Privada": "#6c5ce7"}
    fig2 = px.line(nac_rede, x="ANO", y="MEDIA", color="REDE", markers=True,
                   color_discrete_map=cores_rede,
                   title="Média por Rede de Ensino ao Longo dos Anos")
    fig2.update_traces(line=dict(width=3), marker=dict(size=8))
    fig2.update_layout(height=450, hovermode="x unified", xaxis=dict(dtick=1),
                       margin=dict(l=0, r=0, t=50, b=0))
    st.plotly_chart(fig2, use_container_width=True)

with c4:
    fig_donut = go.Figure(data=[go.Pie(
        labels=gap_rede.sort_values().index, values=gap_rede.sort_values().values,
        marker=dict(colors=[cores_rede[r] for r in gap_rede.sort_values().index]),
        textinfo="label+value", texttemplate="%{label}<br>%{value:.1f}", hole=0.5,
    )])
    fig_donut.update_layout(title="Média Geral por Rede", height=350, margin=dict(l=0, r=0, t=50, b=0),
                            showlegend=False)
    st.plotly_chart(fig_donut, use_container_width=True)

    st.markdown('<div class="insight-box">', unsafe_allow_html=True)
    st.markdown("**  O abismo particular-público**")
    st.markdown(f"""
    Escolas privadas (média **{gap_rede['Privada']:.0f}**) superam as estaduais (**{gap_rede['Estadual']:.0f}**) 
    em **{gap_priv_pub:.0f} pontos**. As federais (**{gap_rede['Federal']:.0f}**) são o melhor da rede pública, 
    quase equiparando-se às privadas.
    """)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")

# ─────────────────────────── CAPÍTULO 2: DESIGUALDADE ───────────────────────────

st.markdown("## ⚖️ Capítulo 2: O Mapa da Desigualdade")
st.markdown("O ENEM revela contrastes profundos entre regiões, redes e localizações.")

# Regiões
c5, c6 = st.columns([2, 1])

with c5:
    cores_regiao = {"Norte": "#2ecc71", "Nordeste": "#e74c3c", "Centro-Oeste": "#f39c12",
                    "Sudeste": "#3498db", "Sul": "#9b59b6"}
    fig3 = px.line(regiao, x="ANO", y="MEDIA", color="REGIAO", markers=True,
                   color_discrete_map=cores_regiao,
                   title="Média por Região Geográfica")
    fig3.update_traces(line=dict(width=3), marker=dict(size=8))
    fig3.update_layout(height=450, hovermode="x unified", xaxis=dict(dtick=1),
                       margin=dict(l=0, r=0, t=50, b=0))
    st.plotly_chart(fig3, use_container_width=True)

with c6:
    media_reg = df.groupby("REGIAO")["MEDIA"].mean().sort_values()
    fig_reg_bar = px.bar(media_reg, x=media_reg.values, y=media_reg.index, orientation="h",
                         color=media_reg.index, color_discrete_map=cores_regiao,
                         text=media_reg.round(1).astype(str))
    fig_reg_bar.update_layout(title="Média Geral por Região", height=350, showlegend=False,
                              xaxis_title="Média", yaxis_title="", margin=dict(l=0, r=0, t=50, b=0))
    fig_reg_bar.update_traces(textposition="outside")
    st.plotly_chart(fig_reg_bar, use_container_width=True)

    diff_sul_norte = media_reg["Sul"] - media_reg["Norte"]
    st.markdown(f'<div class="insight-box">', unsafe_allow_html=True)
    st.markdown(f"**  A diferença regional**")
    st.markdown(f"""
    O **Sul** lidera com **{media_reg['Sul']:.0f}** pontos, enquanto o **Norte** fica com **{media_reg['Norte']:.0f}**.
    A diferença de **{diff_sul_norte:.0f} pontos** entre Sul e Norte é maior que o gap entre 
    federal e estadual — um reflexo das desigualdades estruturais do país.
    """)
    st.markdown("</div>", unsafe_allow_html=True)

# Urbano vs Rural
anos_loc = sorted(df[df["LOCALIZACAO"].notna()]["ANO"].unique())
if len(anos_loc) >= 2:
    st.markdown("###   Urbano vs Rural")
    st.info(f"Dados disponíveis apenas para os anos: {', '.join(str(a) for a in anos_loc)}", icon="ℹ️")
    urb_rural = df.groupby(["ANO", "LOCALIZACAO"])["MEDIA"].mean().reset_index()

    c7, c8 = st.columns([2, 1])

    with c7:
        fig_ur = px.line(urb_rural, x="ANO", y="MEDIA", color="LOCALIZACAO", markers=True,
                         color_discrete_map={"Urbana": "#3498db", "Rural": "#2ecc71"},
                         title="Média: Escolas Urbanas vs Rurais")
        fig_ur.update_traces(line=dict(width=3), marker=dict(size=8))
        fig_ur.update_layout(height=400, hovermode="x unified", xaxis=dict(dtick=1),
                             margin=dict(l=0, r=0, t=50, b=0))
        st.plotly_chart(fig_ur, use_container_width=True)

    with c8:
        med_urb = df[df["LOCALIZACAO"] == "Urbana"]["MEDIA"].mean()
        med_rur = df[df["LOCALIZACAO"] == "Rural"]["MEDIA"].mean()
        gap_ur = med_urb - med_rur
        st.markdown(f'<div class="insight-box">', unsafe_allow_html=True)
        st.markdown(f"**  A fronteira invisível**")
        st.markdown(f"""
        Escolas urbanas (**{med_urb:.0f}**) superam as rurais (**{med_rur:.0f}**) em **{gap_ur:.0f} pontos**.
        O gap urbano-rural é comparável ao gap entre redes federal e municipal.
        """)
        st.markdown("</div>", unsafe_allow_html=True)

        rural_fed = df[(df["LOCALIZACAO"] == "Rural") & (df["DEPENDENCIA"] == "Federal")]["MEDIA"].mean()
        urb_priv = df[(df["LOCALIZACAO"] == "Urbana") & (df["DEPENDENCIA"] == "Privada")]["MEDIA"].mean()
        st.markdown(f'<div class="insight-box">', unsafe_allow_html=True)
        st.markdown(f"**  Onde a rural se destaca?**")
        st.markdown(f"""
        Escolas rurais da rede **Federal** (Institutos Federais no interior) atingem **{rural_fed:.0f} pontos**,
        ante **{urb_priv:.0f}** das urbanas privadas — diferença de **{urb_priv - rural_fed:.0f} pontos**.
        """)
        st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")

# ─────────────────────────── CAPÍTULO 3: PROTAGONISTAS ───────────────────────────

st.markdown("##   Capítulo 3: Os Protagonistas")
st.markdown("Estados e municípios que se destacaram ao longo da década.")

c9, c10 = st.columns(2)

with c9:
    top_uf = uf.groupby("SG_UF_ESC")["MEDIA"].mean().sort_values(ascending=False).head(10)
    bottom_uf = uf.groupby("SG_UF_ESC")["MEDIA"].mean().sort_values().head(5)

    fig_top_uf = px.bar(top_uf, x=top_uf.values, y=top_uf.index, orientation="h",
                        color=top_uf.values, color_continuous_scale="Greens",
                        text=top_uf.round(1).astype(str), title="Top 10 Estados por Média")
    fig_top_uf.update_layout(height=400, yaxis=dict(categoryorder="total ascending"), showlegend=False,
                             margin=dict(l=0, r=0, t=50, b=0))
    fig_top_uf.update_traces(textposition="outside")
    st.plotly_chart(fig_top_uf, use_container_width=True)

with c10:
    fig_bot_uf = px.bar(bottom_uf, x=bottom_uf.values, y=bottom_uf.index, orientation="h",
                        color=bottom_uf.values, color_continuous_scale="Reds_r",
                        text=bottom_uf.round(1).astype(str), title="5 Estados com Menor Média")
    fig_bot_uf.update_layout(height=400, yaxis=dict(categoryorder="total ascending"), showlegend=False,
                             margin=dict(l=0, r=0, t=50, b=0))
    fig_bot_uf.update_traces(textposition="outside")
    st.plotly_chart(fig_bot_uf, use_container_width=True)

# Bump chart: evolução do ranking dos estados
st.markdown("###   Corrida dos Estados: Ranking Ano a Ano")

rank_uf = uf.copy()
rank_uf["RANK"] = rank_uf.groupby("ANO")["MEDIA"].rank(ascending=False)
top_5_uf = rank_uf[rank_uf["SG_UF_ESC"].isin(
    rank_uf.groupby("SG_UF_ESC")["RANK"].mean().nsmallest(7).index
)]

fig_bump = go.Figure()
for est in sorted(top_5_uf["SG_UF_ESC"].unique()):
    d = top_5_uf[top_5_uf["SG_UF_ESC"] == est].sort_values("ANO")
    fig_bump.add_trace(go.Scatter(
        x=d["ANO"], y=d["RANK"], mode="lines+markers+text",
        name=est, text=d["RANK"].astype(int), textposition="middle right",
        line=dict(width=4), marker=dict(size=10),
        hovertemplate="%{x}: %{y:.0f}º lugar<extra></extra>",
    ))
fig_bump.update_layout(title="Ranking dos Melhores Estados (posição 1 = melhor)", height=450,
                       yaxis=dict(autorange="reversed", dtick=1, title="Posição"),
                       xaxis=dict(dtick=1), hovermode="x unified",
                       margin=dict(l=0, r=0, t=50, b=0))
st.plotly_chart(fig_bump, use_container_width=True)

st.markdown("---")

# ─────────────────────────── CAPÍTULO 4: DISCIPLINAS ───────────────────────────

st.markdown("##   Capítulo 4: A Anatomia da Nota")
st.markdown("Como cada disciplina contribui para o resultado final? Onde cada rede se destaca?")

disciplinas = ["LC", "CH", "CN", "MT", "RD"]
labels_disc = {"LC": "Linguagens", "CH": "Humanas", "CN": "Natureza", "MT": "Matemática", "RD": "Redação"}

c11, c12 = st.columns([1.5, 1])

with c11:
    radar_data = rede_ano.groupby("DEPENDENCIA")[disciplinas].mean().reset_index()
    fig_radar = go.Figure()
    for _, row in radar_data.iterrows():
        vals = row[disciplinas].tolist() + [row[disciplinas].tolist()[0]]
        theta = [labels_disc[d] for d in disciplinas] + [labels_disc[disciplinas[0]]]
        fig_radar.add_trace(go.Scatterpolar(
            r=vals, theta=theta, name=row["DEPENDENCIA"],
            line=dict(width=3, color=cores_rede.get(row["DEPENDENCIA"], "#fff")),
            marker=dict(size=6),
        ))
    fig_radar.update_layout(title="Perfil de Desempenho por Rede (Radar)", height=450,
                            polar=dict(radialaxis=dict(visible=True, range=[450, 700])),
                            margin=dict(l=80, r=80, t=50, b=0))
    st.plotly_chart(fig_radar, use_container_width=True)

with c12:
    maior_var = rede_ano.groupby("DEPENDENCIA")[disciplinas].std().mean(axis=0).sort_values(ascending=False)
    fig_var = px.bar(maior_var, x=maior_var.values, y=[labels_disc[d] for d in maior_var.index],
                     orientation="h", color=maior_var.values, color_continuous_scale="Viridis",
                     title="Disciplinas com Maior Variação entre Redes")
    fig_var.update_layout(height=350, showlegend=False, yaxis_title="", xaxis_title="Desvio Padrão",
                          margin=dict(l=0, r=0, t=50, b=0))
    st.plotly_chart(fig_var, use_container_width=True)

    st.markdown('<div class="insight-box">', unsafe_allow_html=True)
    st.markdown("**  Redação: o grande divisor**")
    st.markdown("""
    Redação (**RD**) é a disciplina com maior dispersão entre as redes — 
    é onde a desigualdade educacional mais aparece. Escolas privadas 
    investem pesado em treino de redação; públicas, nem sempre.
    """)
    st.markdown("</div>", unsafe_allow_html=True)

# Scatter plot: Mat x LC
st.markdown("###   Matemática vs Linguagens: O Perfil das Redes")

ano_scatter = st.selectbox("Ano para análise", sorted(df["ANO"].unique()), key="scatter_ano")
df_scatter = df[df["ANO"] == ano_scatter].groupby(["DEPENDENCIA", "NO_MUNICIPIO_ESC", "SG_UF_ESC"]).agg(
    MT=("MT", "mean"), LC=("LC", "mean"), MEDIA=("MEDIA", "mean"), ESCOLAS=("MEDIA", "count")
).reset_index()

fig_scatter = px.scatter(
    df_scatter, x="LC", y="MT", color="DEPENDENCIA", size="ESCOLAS",
    color_discrete_map=cores_rede,
    hover_name="NO_MUNICIPIO_ESC", hover_data={"SG_UF_ESC": True, "MEDIA": ":.1f", "ESCOLAS": True},
    title=f"Matemática vs Linguagens por Município — {ano_scatter}",
    labels={"LC": "Linguagens (média)", "MT": "Matemática (média)", "DEPENDENCIA": "Rede"},
    size_max=20, opacity=0.6,
)
fig_scatter.add_hline(y=df_scatter["MT"].mean(), line_dash="dash", line_color="gray", opacity=0.5)
fig_scatter.add_vline(x=df_scatter["LC"].mean(), line_dash="dash", line_color="gray", opacity=0.5)
fig_scatter.update_layout(height=500, margin=dict(l=0, r=0, t=50, b=0))
st.plotly_chart(fig_scatter, use_container_width=True)

st.markdown("---")

# ─────────────────────────── CAPÍTULO 5: GAP EVOLUTION ───────────────────────────

st.markdown("##   Capítulo 5: A Evolução do Gap")
st.markdown("As desigualdades estão aumentando ou diminuindo com o tempo?")

c13, c14 = st.columns(2)

with c13:
    gap_ano = nac_rede.pivot(index="ANO", columns="REDE", values="MEDIA").reset_index()
    gap_ano["GAP_PRIV_PUB"] = gap_ano["Privada"] - gap_ano["Estadual"]
    gap_ano["GAP_FED_EST"] = gap_ano["Federal"] - gap_ano["Estadual"]

    fig_gap1 = go.Figure()
    fig_gap1.add_trace(go.Scatter(x=gap_ano["ANO"], y=gap_ano["GAP_PRIV_PUB"], mode="lines+markers",
                                  name="Privada − Estadual", line=dict(color="#e94560", width=3),
                                  fill="tozeroy", fillcolor="rgba(233,69,96,0.15)"))
    fig_gap1.add_trace(go.Scatter(x=gap_ano["ANO"], y=gap_ano["GAP_FED_EST"], mode="lines+markers",
                                  name="Federal − Estadual", line=dict(color="#4ecdc4", width=3),
                                  fill="tozeroy", fillcolor="rgba(78,205,196,0.15)"))
    fig_gap1.update_layout(title="Evolução do Gap entre Redes", height=400,
                           xaxis=dict(dtick=1), hovermode="x unified",
                           margin=dict(l=0, r=0, t=50, b=0))
    st.plotly_chart(fig_gap1, use_container_width=True)

with c14:
    gap_reg = regiao.pivot(index="ANO", columns="REGIAO", values="MEDIA")
    fig_gap2 = go.Figure()
    for reg in ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]:
        fig_gap2.add_trace(go.Scatter(
            x=gap_reg.index, y=gap_reg[reg] - gap_reg["Sul"],
            mode="lines+markers", name=f"{reg} − Sul",
            line=dict(width=2, color=cores_regiao.get(reg)),
        ))
    fig_gap2.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.3)
    fig_gap2.update_layout(title="Diferença em relação à Região Sul (referência)", height=400,
                           xaxis=dict(dtick=1), hovermode="x unified",
                           margin=dict(l=0, r=0, t=50, b=0))
    st.plotly_chart(fig_gap2, use_container_width=True)

gap_priv_pub_anos = nac_rede.pivot(index="ANO", columns="REDE", values="MEDIA")
gap_priv_pub_anos["GAP"] = gap_priv_pub_anos["Privada"] - gap_priv_pub_anos["Estadual"]
gap_priv_pub_anos["GAP_FED"] = gap_priv_pub_anos["Privada"] - gap_priv_pub_anos["Federal"]
gap_min = gap_priv_pub_anos["GAP"].min()
gap_max = gap_priv_pub_anos["GAP"].max()
gap_fed_2014 = gap_priv_pub_anos.loc[2014, "GAP_FED"]
gap_fed_2025 = gap_priv_pub_anos.loc[2025, "GAP_FED"]
st.markdown('<div class="insight-box">', unsafe_allow_html=True)
st.markdown("**  O gap estável**")
st.markdown(f"""
Ao contrário do que se poderia esperar, o gap entre redes privada e pública **não diminuiu** 
em 12 anos — variou de {gap_min:.0f} a {gap_max:.0f} pontos (em 2025: {gap_priv_pub_anos.loc[2025, 'GAP']:.0f} pts). 
As federais, porém, reduziram a distância para as privadas de {gap_fed_2014:.0f} para {gap_fed_2025:.0f} pontos.

Já o abismo regional **aumentou**: Norte e Nordeste perderam terreno relativo para o Sul 
na segunda metade da década.
""")
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")

# ─────────────────────────── CAPÍTULO 6: MUNICÍPIOS ───────────────────────────

st.markdown("##   Capítulo 6: Onde o Brasil Aprende Melhor")
st.markdown("Os municípios que mais se destacaram — e os que mais evoluíram.")

c15, c16 = st.columns(2)

with c15:
    top_mun = tab_completa.groupby(["NO_MUNICIPIO_ESC", "SG_UF_ESC"])["MEDIA"].mean().reset_index()
    top10 = top_mun.sort_values("MEDIA", ascending=False).head(10)
    top10["MUN"] = top10["NO_MUNICIPIO_ESC"] + " - " + top10["SG_UF_ESC"]

    fig_top10 = px.bar(top10, x="MEDIA", y="MUN", orientation="h",
                       color="MEDIA", color_continuous_scale="Greens",
                       text=top10["MEDIA"].round(1).astype(str))
    fig_top10.update_layout(title="Top 10 Municípios (média 2014-2025)", height=400,
                            yaxis=dict(categoryorder="total ascending"), showlegend=False,
                            margin=dict(l=0, r=0, t=50, b=0))
    fig_top10.update_traces(textposition="outside")
    st.plotly_chart(fig_top10, use_container_width=True)

with c16:
    mun_fed = tab_completa[tab_completa["DEPENDENCIA"] == "Federal"]
    top_fed = mun_fed.groupby(["NO_MUNICIPIO_ESC", "SG_UF_ESC"])["MEDIA"].mean().reset_index()
    top_fed = top_fed.sort_values("MEDIA", ascending=False).head(10)
    top_fed["MUN"] = top_fed["NO_MUNICIPIO_ESC"] + " - " + top_fed["SG_UF_ESC"]

    fig_top_fed = px.bar(top_fed, x="MEDIA", y="MUN", orientation="h",
                         color="MEDIA", color_continuous_scale="Reds",
                         text=top_fed["MEDIA"].round(1).astype(str))
    fig_top_fed.update_layout(title="Top 10 — Rede Federal (média 2014-2025)", height=400,
                              yaxis=dict(categoryorder="total ascending"), showlegend=False,
                              margin=dict(l=0, r=0, t=50, b=0))
    fig_top_fed.update_traces(textposition="outside")
    st.plotly_chart(fig_top_fed, use_container_width=True)

# Maiores evolutores
st.markdown("###   Quem Mais Evoluiu?")

evol = tab_completa.groupby(["NO_MUNICIPIO_ESC", "SG_UF_ESC", "ANO"])["MEDIA"].mean().reset_index()
evol_pivot = evol.pivot(index=["NO_MUNICIPIO_ESC", "SG_UF_ESC"], columns="ANO", values="MEDIA")

evol_list = []
for idx in evol_pivot.index:
    row = evol_pivot.loc[idx]
    valid = row.dropna()
    if len(valid) >= 2:
        first_ano = int(valid.index[0])
        last_ano = int(valid.index[-1])
        evol_list.append({
            "NO_MUNICIPIO_ESC": idx[0],
            "SG_UF_ESC": idx[1],
            "PRIMEIRO_ANO": first_ano,
            "ULTIMO_ANO": last_ano,
            "MEDIA_INI": valid.iloc[0],
            "MEDIA_FIM": valid.iloc[-1],
            "EVOLUCAO": valid.iloc[-1] - valid.iloc[0],
        })

top_evol = pd.DataFrame(evol_list).sort_values("EVOLUCAO", ascending=False).head(10)
top_evol["MUN"] = top_evol["NO_MUNICIPIO_ESC"] + " - " + top_evol["SG_UF_ESC"]
top_evol["ROTULO"] = top_evol.apply(
    lambda r: f"{r['EVOLUCAO']:.1f} ({r['PRIMEIRO_ANO']}→{r['ULTIMO_ANO']})", axis=1
)

fig_evol = px.bar(top_evol, x="EVOLUCAO", y="MUN", orientation="h",
                  color="EVOLUCAO", color_continuous_scale="Blues",
                  text=top_evol["ROTULO"])
fig_evol.update_layout(title="Municípios com Maior Evolução (primeiro → último ano disponível)", height=400,
                       yaxis=dict(categoryorder="total ascending"), showlegend=False,
                       margin=dict(l=0, r=0, t=50, b=0))
fig_evol.update_traces(textposition="outside")
st.plotly_chart(fig_evol, use_container_width=True)

st.markdown("---")

# ─────────────────────────── CAPÍTULO 7: O FUTURO ───────────────────────────

st.markdown("##   Capítulo 7: Tendências e o Futuro")
st.markdown("O que os dados sugerem para os próximos anos?")

c17, c18 = st.columns([2, 1])

with c17:
    x_anos = nac["ANO"].values
    y_media = nac["MEDIA"].values
    coefs = np.polyfit(x_anos, y_media, 1)
    trend = np.poly1d(coefs)
    x_futuro = np.arange(2014, 2031)
    y_futuro = trend(x_futuro)

    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(x=nac["ANO"], y=nac["MEDIA"], mode="markers",
                                   marker=dict(size=10, color="#4ecdc4"),
                                   name="Real", hovertemplate="%{x}: %{y:.1f}<extra></extra>"))
    fig_trend.add_trace(go.Scatter(x=x_futuro, y=y_futuro, mode="lines",
                                   line=dict(color="#e94560", width=3, dash="dash"),
                                   name="Tendência Linear"))
    fig_trend.add_trace(go.Scatter(
        x=x_futuro[x_futuro > 2025], y=y_futuro[x_futuro > 2025],
        mode="lines+markers", line=dict(color="#e94560", width=3, dash="dot"),
        marker=dict(symbol="star", size=12, color="#ffd93d"),
        name="Projeção", showlegend=True,
    ))
    fig_trend.update_layout(title="Projeção da Média Nacional (regressão linear)", height=450,
                            xaxis=dict(dtick=1), hovermode="x unified",
                            margin=dict(l=0, r=0, t=50, b=0))

    for a in [2028, 2030]:
        y_val = trend(a)
        fig_trend.add_annotation(x=a, y=y_val, text=f"<b>{y_val:.0f}</b>",
                                 showarrow=True, arrowhead=3, ax=0, ay=-30,
                                 font=dict(size=11, color="#ffd93d"))
    st.plotly_chart(fig_trend, use_container_width=True)

with c18:
    target_2030 = trend(2030)
    current = nac_idx.loc[2025]
    needed = target_2030 - current
    st.markdown(f'<div class="insight-box">', unsafe_allow_html=True)
    st.markdown(f"**  Projeção para 2030**")
    st.markdown(f"""
    Se a tendência se mantiver, o Brasil pode atingir **{target_2030:.0f} pontos** em 2030.
    Isso representa um avanço de **{needed:.0f} pontos** em 5 anos — plausível, 
    mas exigirá investimento consistente.
    """)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(f'<div class="insight-box">', unsafe_allow_html=True)
    st.markdown(f"**  O que pode acelerar?**")
    st.markdown("""
    • Expansão dos Institutos Federais (rede que mais se aproxima da privada)
    • Redução do gap regional com foco em Norte/Nordeste
    • Melhoria no ensino de Redação e Matemática nas redes públicas
    """)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")
st.markdown(f"""
<div style="text-align:center; color:#666; font-size:0.85rem; padding:1rem;">
    Dashboard feito com dados do ENEM/INEP (2014–2025) — {datetime.now().strftime('%B %Y')}<br>
    Cada ponto representa a média das escolas de um município disponibilizados pelo INEP em 
    https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem. Mais de {len(df):,} registros analisados.<br>
    Desenvolvido por luciano.espiriao@ifmg.edu.br. 2026 - Todos os direitos reservados.
</div>
""", unsafe_allow_html=True)
