import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from dados_compartilhados import carregar_dados, carregar_campi_if, preparar_dados_if

st.markdown("""
<style>
    .title { font-size: 3rem; font-weight: 800; letter-spacing: -1px; margin-bottom: 0; }
    .subtitle { font-size: 1.1rem; color: #888; margin-top: 0; }
    .kpi-card { background: #0e1117; border: 1px solid #333; border-radius: 12px; padding: 1.2rem 1.5rem; text-align: center; }
    .kpi-value { font-size: 2.2rem; font-weight: 700; }
    .kpi-label { font-size: 0.8rem; color: #888; text-transform: uppercase; letter-spacing: 1px; }
    .insight-ifmg { background: linear-gradient(135deg, #1a1a2e, #16213e); border-left: 4px solid #2ecc71; border-radius: 8px; padding: 1rem 1.5rem; margin: 1rem 0; }
    .insight-ifmg h4 { color: #2ecc71; margin: 0 0 0.3rem 0; }
    .insight-ifmg p { margin: 0; color: #ccc; }
    .ifmg-green { color: #2ecc71; font-weight: 700; }
    h2 { margin-top: 0.5rem; }
</style>
""", unsafe_allow_html=True)

with st.spinner("Carregando dados..."):
    df = carregar_dados()
    campi = carregar_campi_if()
    df_if = preparar_dados_if(df, campi)

if df_if.empty:
    st.warning("Nenhum dado encontrado.")
    st.stop()

df_if_fed = df_if[df_if["DEPENDENCIA"] == "Federal"].copy()
df_ifmg = df_if_fed[df_if_fed["INSTITUTO"] == "IFMG"].copy()
df_outros = df_if_fed[df_if_fed["INSTITUTO"] != "IFMG"].copy()

if df_ifmg.empty:
    st.warning("Nenhum dado encontrado para o IFMG.")
    st.stop()

media_ifmg = df_ifmg["MEDIA"].mean()
media_outros = df_outros["MEDIA"].mean()
media_federal_br = df[df["DEPENDENCIA"] == "Federal"]["MEDIA"].mean()
diff_vs_outros = media_ifmg - media_outros
total_campi_ifmg = df_ifmg["CAMPUS"].nunique()

st.markdown('<p class="title">   IFMG vs Demais Institutos Federais</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">   Comparação detalhada do IFMG com todos os outros Institutos Federais do Brasil no ENEM 2014–2025</p>', unsafe_allow_html=True)

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.markdown(f"""<div class="kpi-card"><div class="kpi-value ifmg-green">{media_ifmg:.1f}</div><div class="kpi-label">Média IFMG</div></div>""", unsafe_allow_html=True)
with k2:
    st.markdown(f"""<div class="kpi-card"><div class="kpi-value" style="color:{'#2ecc71' if diff_vs_outros > 0 else '#e74c3c'}">{diff_vs_outros:+.1f}</div><div class="kpi-label">IFMG vs Demais IFs</div></div>""", unsafe_allow_html=True)
with k3:
    st.markdown(f"""<div class="kpi-card"><div class="kpi-value" style="color:#3498db">{media_outros:.1f}</div><div class="kpi-label">Média Demais IFs</div></div>""", unsafe_allow_html=True)
with k4:
    st.markdown(f"""<div class="kpi-card"><div class="kpi-value" style="color:#f39c12">{total_campi_ifmg}</div><div class="kpi-label">Campi IFMG</div></div>""", unsafe_allow_html=True)
with k5:
    st.markdown(f"""<div class="kpi-card"><div class="kpi-value">{len(df_ifmg):,}</div><div class="kpi-label">Registros IFMG</div></div>""", unsafe_allow_html=True)

st.markdown("---")
st.markdown("## 📈 Evolução: IFMG vs Demais IFs")
st.markdown("Como o IFMG se comportou ao longo dos anos em comparação com os outros institutos?")

nac_fed_br = df[df["DEPENDENCIA"] == "Federal"].groupby("ANO").agg(MEDIA=("MEDIA", "mean")).reset_index()
ifmg_ano = df_ifmg.groupby("ANO").agg(MEDIA=("MEDIA", "mean"), ESCOLAS=("MEDIA", "count")).reset_index()
outros_ano = df_outros.groupby("ANO").agg(MEDIA=("MEDIA", "mean"), ESCOLAS=("MEDIA", "count")).reset_index()

c1, c2 = st.columns([2, 1])
with c1:
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=outros_ano["ANO"], y=outros_ano["MEDIA"], mode="lines+markers",
        name="Demais IFs", line=dict(color="#e74c3c", width=2, dash="dash"), marker=dict(size=6)))
    fig1.add_trace(go.Scatter(x=ifmg_ano["ANO"], y=ifmg_ano["MEDIA"], mode="lines+markers",
        name="IFMG", line=dict(color="#2ecc71", width=4), marker=dict(size=10)))
    fig1.add_trace(go.Scatter(x=nac_fed_br["ANO"] if 'nac_fed_br' in dir() else [],
        y=nac_fed_br["MEDIA"] if 'nac_fed_br' in dir() else [],
        mode="lines", name="Brasil (Federal)", line=dict(color="#888", width=2, dash="dot")))
    fig1.update_layout(title="Evolução da Média: IFMG vs Demais IFs", height=450,
        hovermode="x unified", xaxis=dict(dtick=1), margin=dict(l=0, r=0, t=50, b=0))
    st.plotly_chart(fig1, use_container_width=True)

with c2:
    st.markdown('<div class="insight-ifmg">', unsafe_allow_html=True)
    st.markdown("**⚔️  IFMG vs Demais**")
    st.markdown(f"""O IFMG supera a média dos demais institutos em **{diff_vs_outros:.1f} pontos**.<br>
    Diferença vs Brasil Federal: **{media_ifmg - media_federal_br:+.1f}**.""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if not ifmg_ano.empty:
        evol_ifmg = ifmg_ano["MEDIA"].iloc[-1] - ifmg_ano["MEDIA"].iloc[0]
        evol_outros = outros_ano["MEDIA"].iloc[-1] - outros_ano["MEDIA"].iloc[0]
        st.markdown('<div class="insight-ifmg">', unsafe_allow_html=True)
        st.markdown("**📈  Evolução (todo período)**")
        st.markdown(f"""IFMG: **{evol_ifmg:+.1f}** pontos | Demais IFs: **{evol_outros:+.1f}** pontos""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")
st.markdown("## 🏆 Comparativo por Instituto")
st.markdown("Onde o IFMG se posiciona no ranking geral dos institutos federais?")

comp_if = df_if_fed.groupby("INSTITUTO").agg(
    MEDIA=("MEDIA", "mean"), CAMPI=("CAMPUS", "nunique"), REGISTROS=("MEDIA", "count")
).reset_index().sort_values("MEDIA", ascending=False)

comp_if["COR"] = comp_if["INSTITUTO"].apply(lambda x: "#2ecc71" if x == "IFMG" else "#e74c3c")
fig_rank = go.Figure()
fig_rank.add_trace(go.Bar(
    x=comp_if["MEDIA"], y=comp_if["INSTITUTO"], orientation="h",
    marker_color=comp_if["COR"], text=comp_if["MEDIA"].round(1).astype(str),
    hovertemplate="%{y}: %{x:.1f}<extra></extra>",
))
fig_rank.update_layout(title="Ranking: IFMG vs Demais Institutos", height=500,
    yaxis=dict(categoryorder="total ascending"), showlegend=False,
    xaxis_title="Média Geral", margin=dict(l=0, r=0, t=50, b=0))
fig_rank.update_traces(textposition="outside")
st.plotly_chart(fig_rank, use_container_width=True)

pos_ifmg = comp_if["INSTITUTO"].tolist().index("IFMG") + 1
st.markdown(f'<div class="insight-ifmg">', unsafe_allow_html=True)
st.markdown(f"**🎯  Posição do IFMG**")
st.markdown(f"""O IFMG ocupa a **{pos_ifmg}ª posição** entre {len(comp_if)} institutos federais, com média **{media_ifmg:.1f}**.""", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")
st.markdown("## 📊 Gap: Campi do IFMG vs Média dos Demais IFs")
st.markdown("Quanto cada campus do IFMG supera (ou fica abaixo) da média dos outros institutos federais?")

campus_ifmg = df_ifmg.groupby("CAMPUS")["MEDIA"].mean().reset_index()
gap_campus = campus_ifmg.copy()
gap_campus["GAP"] = gap_campus["MEDIA"] - media_outros
gap_campus = gap_campus.sort_values("GAP", ascending=False)

fig_gap = go.Figure()
fig_gap.add_trace(go.Bar(
    x=gap_campus["CAMPUS"], y=gap_campus["GAP"],
    marker_color=gap_campus["GAP"].apply(lambda x: "#2ecc71" if x >= 0 else "#e74c3c"),
    hovertemplate="%{x}: %{y:+.1f}<extra></extra>",
))
fig_gap.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.3)
fig_gap.update_layout(title="Quanto cada campus do IFMG supera (ou fica abaixo) da média dos demais IFs",
    height=400, xaxis_tickangle=-45, margin=dict(l=0, r=0, t=50, b=0))
st.plotly_chart(fig_gap, use_container_width=True)

if not gap_campus.empty:
    melhor = gap_campus.iloc[0]
    pior = gap_campus.iloc[-1]
    st.markdown(f'<div class="insight-ifmg">', unsafe_allow_html=True)
    st.markdown(f"**⭐  Destaques**")
    st.markdown(f"""Melhor: **{melhor['CAMPUS']}** ({melhor['GAP']:+.1f} pts acima da média dos demais IFs)<br>
    Maior desafio: **{pior['CAMPUS']}** ({pior['GAP']:+.1f} pts abaixo)""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")
st.markdown("## 🔬 Perfil por Disciplina")
st.markdown("Como IFMG e demais IFs se comparam em cada disciplina?")

disciplinas = ["LC", "CH", "CN", "MT", "RD"]
labels_disc = {"LC": "Linguagens", "CH": "Humanas", "CN": "Natureza", "MT": "Matemática", "RD": "Redação"}

disc_ifmg = df_ifmg[disciplinas].mean()
disc_outros = df_outros[disciplinas].mean()

c7, c8 = st.columns([1.5, 1])
with c7:
    fig_radar = go.Figure()
    for nome, data in [("IFMG", disc_ifmg), ("Demais IFs", disc_outros)]:
        vals = data.tolist() + [data.tolist()[0]]
        theta = [labels_disc[d] for d in disciplinas] + [labels_disc[disciplinas[0]]]
        fig_radar.add_trace(go.Scatterpolar(r=vals, theta=theta, name=nome,
            line=dict(width=3, color="#2ecc71" if nome == "IFMG" else "#e74c3c"), fill="toself" if nome == "IFMG" else None, opacity=0.7))
    fig_radar.update_layout(title="Perfil por Disciplina", height=450,
        polar=dict(radialaxis=dict(visible=True, range=[450, 750])), margin=dict(l=80, r=80, t=50, b=0))
    st.plotly_chart(fig_radar, use_container_width=True)

with c8:
    disc_comp = pd.DataFrame({"IFMG": disc_ifmg, "Demais IFs": disc_outros, "Diferença": disc_ifmg - disc_outros})
    fig_disc = go.Figure()
    fig_disc.add_trace(go.Bar(name="IFMG", x=[labels_disc[d] for d in disciplinas], y=disc_ifmg.values,
        marker_color="#2ecc71", hovertemplate="%{x}: %{y:.1f}<extra></extra>"))
    fig_disc.add_trace(go.Bar(name="Demais IFs", x=[labels_disc[d] for d in disciplinas], y=disc_outros.values,
        marker_color="#e74c3c", hovertemplate="%{x}: %{y:.1f}<extra></extra>"))
    fig_disc.update_layout(title="Comparação por Disciplina", height=400, barmode="group", margin=dict(l=0, r=0, t=50, b=0))
    st.plotly_chart(fig_disc, use_container_width=True)

    maior_vantagem = disc_comp["Diferença"].idxmax()
    maior_desafio = disc_comp["Diferença"].idxmin()
    st.markdown('<div class="insight-ifmg">', unsafe_allow_html=True)
    st.markdown("**📚  Disciplinas**")
    st.markdown(f"""Maior vantagem: **{labels_disc[maior_vantagem]}** ({disc_comp.loc[maior_vantagem, 'Diferença']:+.1f} pts)<br>
    Maior desafio: **{labels_disc[maior_desafio]}** ({disc_comp.loc[maior_desafio, 'Diferença']:+.1f} pts)""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")
st.markdown("## 🥇 Rankings dos Campi IFMG")
st.markdown("Desempenho individual de cada campus do IFMG.")

ano_sel = st.selectbox("📅 Ano", sorted(df["ANO"].unique()), key="ano_ifmg_vs")
campus_ano = df_ifmg[df_ifmg["ANO"] == ano_sel].groupby("CAMPUS").agg(
    MEDIA=("MEDIA", "mean"), LC=("LC", "mean"), CH=("CH", "mean"),
    CN=("CN", "mean"), MT=("MT", "mean"), RD=("RD", "mean"), ESCOLAS=("MEDIA", "count"),
).reset_index().sort_values("MEDIA", ascending=False)

if not campus_ano.empty:
    fig_campus = px.bar(campus_ano, x="MEDIA", y="CAMPUS", orientation="h",
        color="MEDIA", color_continuous_scale="Greens",
        text=campus_ano["MEDIA"].round(1).astype(str), title=f"Campi IFMG em {ano_sel}")
    fig_campus.update_layout(height=450, yaxis=dict(categoryorder="total ascending"), showlegend=False, margin=dict(l=0, r=0, t=50, b=0))
    fig_campus.update_traces(textposition="outside")
    st.plotly_chart(fig_campus, use_container_width=True)

st.markdown("---")
st.markdown("## 📋 Tabela Comparativa IFMG vs Brasil")
st.markdown("Desempenho do IFMG por ano.")

tab_ifmg_ano = df_ifmg.groupby("ANO").agg(
    MEDIA_IFMG=("MEDIA", "mean"), LC=("LC", "mean"), CH=("CH", "mean"),
    CN=("CN", "mean"), MT=("MT", "mean"), RD=("RD", "mean"), CAMPI=("CAMPUS", "nunique"),
).reset_index()

tab_outros_ano = df_outros.groupby("ANO").agg(MEDIA_OUTROS=("MEDIA", "mean")).reset_index()

tab_comp = tab_ifmg_ano.merge(tab_outros_ano, on="ANO", how="left")
tab_comp["DIFERENCA"] = tab_comp["MEDIA_IFMG"] - tab_comp["MEDIA_OUTROS"]
tab_comp.columns = ["Ano", "Média IFMG", "LC", "CH", "CN", "MT", "RD", "Campi", "Média Demais IFs", "Diferença"]

st.dataframe(
    tab_comp.style.format({
        "Média IFMG": "{:.2f}", "LC": "{:.1f}", "CH": "{:.1f}", "CN": "{:.1f}", "MT": "{:.1f}", "RD": "{:.1f}",
        "Média Demais IFs": "{:.2f}", "Diferença": "{:+.2f}",
    }),
    use_container_width=True, height=400,
)

csv = tab_comp.to_csv(index=False, sep=";", decimal=",")
st.download_button("Exportar CSV", data=csv, file_name="ifmg_vs_demais_ifs.csv", mime="text/csv")

st.markdown("---")
st.markdown(f"""
<div style="text-align:center; color:#666; font-size:0.85rem; padding:1rem;">
    Dashboard IFMG vs Demais IFs no ENEM — Dados ENEM/INEP (2014–2025) | {datetime.now().strftime('%B %Y')}<br>
    {total_campi_ifmg} campi do IFMG analisados em comparação com {df_outros['INSTITUTO'].nunique()} outros institutos federais.<br>
    Desenvolvido por luciano.espiriao@ifmg.edu.br. 2026 - Todos os direitos reservados.
</div>
""", unsafe_allow_html=True)
