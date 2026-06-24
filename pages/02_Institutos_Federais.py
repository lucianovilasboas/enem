import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from dados_compartilhados import carregar_dados, carregar_rede_federal, preparar_dados_rede_federal, carregar_campi_if
import util

st.markdown("""
<style>
    .title { font-size: 3rem; font-weight: 800; letter-spacing: -1px; margin-bottom: 0; }
    .subtitle { font-size: 1.1rem; color: #888; margin-top: 0; }
    .kpi-card { background: #0e1117; border: 1px solid #333; border-radius: 12px; padding: 1.2rem 1.5rem; text-align: center; }
    .kpi-value { font-size: 2.2rem; font-weight: 700; }
    .kpi-label { font-size: 0.8rem; color: #888; text-transform: uppercase; letter-spacing: 1px; }
    .insight-green { background: linear-gradient(135deg, #1a1a2e, #16213e); border-left: 4px solid #2ecc71; border-radius: 8px; padding: 1rem 1.5rem; margin: 1rem 0; }
    .insight-green h4 { color: #2ecc71; margin: 0 0 0.3rem 0; }
    .insight-green p { margin: 0; color: #ccc; }
    h2 { margin-top: 0.5rem; }
</style>
""", unsafe_allow_html=True)

with st.spinner("Carregando dados..."):
    df = carregar_dados()
    campi_rede = carregar_rede_federal()
    df_rede = preparar_dados_rede_federal(df, campi_rede)

if df_rede.empty:
    st.warning("Nenhum dado encontrado para a Rede Federal no período.")
    st.stop()

df_rede_fed = df_rede[df_rede["DEPENDENCIA"] == "Federal"].copy()

# Sidebar filters
st.sidebar.header("🔍 Filtros")

tipos_disponiveis = sorted(df_rede_fed["TIPO_INSTITUICAO"].unique())
tipo_map = {"IF": "Institutos Federais", "CEFET": "CEFETs", "CPII": "Colégio Pedro II", "UTFPR": "UTFPR", "ETV": "Escolas Técnicas Vinculadas"}
tipos_sel = st.sidebar.multiselect("🏫 Tipo de Instituição", tipos_disponiveis,
    format_func=lambda x: tipo_map.get(x, x), default=tipos_disponiveis)

if tipos_sel:
    df_filtrado = df_rede_fed[df_rede_fed["TIPO_INSTITUICAO"].isin(tipos_sel)]
else:
    df_filtrado = df_rede_fed

lista_instituicoes = sorted(df_filtrado["INSTITUICAO"].unique())
inst_selecionado = st.sidebar.selectbox("🏛️ Instituição", ["Todas"] + lista_instituicoes, key="if_selector")

if inst_selecionado != "Todas":
    df_inst = df_filtrado[df_filtrado["INSTITUICAO"] == inst_selecionado]
else:
    df_inst = df_filtrado

media_geral = df_inst["MEDIA"].mean()
media_federal_br = df[df["DEPENDENCIA"] == "Federal"]["MEDIA"].mean()
total_campi = df_inst["CAMPUS"].nunique()
total_inst = df_inst["INSTITUICAO"].nunique() if inst_selecionado == "Todas" else 1
total_reg = len(df_inst)

st.markdown('<p class="title">   Rede Federal no ENEM</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">   O desempenho de toda a Rede Federal de Educação, Ciência e Tecnologia no ENEM 2014–2025</p>', unsafe_allow_html=True)

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.markdown(f"""<div class="kpi-card"><div class="kpi-value" style="color:#2ecc71">{media_geral:.1f}</div><div class="kpi-label">Média</div></div>""", unsafe_allow_html=True)
with k2:
    diff_br = media_geral - media_federal_br
    cor = "#2ecc71" if diff_br >= 0 else "#e74c3c"
    st.markdown(f"""<div class="kpi-card"><div class="kpi-value" style="color:{cor}">{diff_br:+.1f}</div><div class="kpi-label">vs Média Federal BR</div></div>""", unsafe_allow_html=True)
with k3:
    st.markdown(f"""<div class="kpi-card"><div class="kpi-value" style="color:#3498db">{media_federal_br:.1f}</div><div class="kpi-label">Média Federal Brasil</div></div>""", unsafe_allow_html=True)
with k4:
    st.markdown(f"""<div class="kpi-card"><div class="kpi-value" style="color:#f39c12">{total_campi}</div><div class="kpi-label">Campi</div></div>""", unsafe_allow_html=True)
with k5:
    st.markdown(f"""<div class="kpi-card"><div class="kpi-value">{total_reg:,}</div><div class="kpi-label">Registros</div></div>""", unsafe_allow_html=True)

st.markdown("---")
st.markdown("## 📊 Panorama da Rede Federal")
st.markdown("Como as instituições se posicionam frente à média da rede federal brasileira?")

nac_inst = df_inst.groupby("ANO").agg(MEDIA=("MEDIA", "mean"), ESCOLAS=("MEDIA", "count")).reset_index()
nac_fed_br = df[df["DEPENDENCIA"] == "Federal"].groupby("ANO").agg(MEDIA=("MEDIA", "mean")).reset_index()

c1, c2 = st.columns([2, 1])
with c1:
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=nac_fed_br["ANO"], y=nac_fed_br["MEDIA"], mode="lines+markers",
        name="Brasil (Rede Federal)", line=dict(color="#e74c3c", width=2, dash="dash"), marker=dict(size=6)))
    fig1.add_trace(go.Scatter(x=nac_inst["ANO"], y=nac_inst["MEDIA"], mode="lines+markers",
        name=inst_selecionado if inst_selecionado != "Todas" else "Selecionado", line=dict(color="#2ecc71", width=4), marker=dict(size=10)))
    fig1.update_layout(title="Evolução da Média no ENEM", height=450, hovermode="x unified", xaxis=dict(dtick=1), margin=dict(l=0, r=0, t=50, b=0))
    st.plotly_chart(fig1, use_container_width=True)

with c2:
    st.markdown('<div class="insight-green">', unsafe_allow_html=True)
    st.markdown("**  Desempenho**")
    if diff_br >= 0:
        st.markdown(f"""A seleção atual supera a média da rede federal brasileira em **{diff_br:.1f} pontos**.""")
    else:
        st.markdown(f"""A seleção atual fica **{abs(diff_br):.1f} pontos abaixo** da média da rede federal brasileira.""")
    st.markdown("</div>", unsafe_allow_html=True)
    if inst_selecionado == "Todas":
        top_inst = df_inst.groupby("INSTITUICAO")["MEDIA"].mean().sort_values(ascending=False).head(5)
        st.markdown('<div class="insight-green">', unsafe_allow_html=True)
        st.markdown("**  Top 5 Instituições**")
        for i, (inst, media) in enumerate(top_inst.items(), 1):
            st.markdown(f"{i}. **{inst}** — {media:.1f}")
        st.markdown("</div>", unsafe_allow_html=True)

if inst_selecionado == "Todas":
    st.markdown("### 🏆 Ranking das Instituições")
    rank_inst = df_inst.groupby("INSTITUICAO").agg(
        MEDIA=("MEDIA", "mean"), TIPO=("TIPO_INSTITUICAO", "first"),
        CAMPI=("CAMPUS", "nunique"), REGISTROS=("MEDIA", "count")
    ).reset_index().sort_values("MEDIA", ascending=False)
    fig_rank = px.bar(rank_inst, x="MEDIA", y="INSTITUICAO", orientation="h",
        color="TIPO", text=rank_inst["MEDIA"].round(1).astype(str) + " (" + rank_inst["CAMPI"].astype(str) + " campi)",
        title="Média Geral por Instituição (2014-2025)",
        color_discrete_map={"IF": "#2ecc71", "CEFET": "#3498db", "CPII": "#f39c12",
                            "UTFPR": "#9b59b6", "ETV": "#e74c3c"})
    fig_rank.update_layout(height=500, yaxis=dict(categoryorder="total ascending"), showlegend=True, margin=dict(l=0, r=0, t=50, b=0))
    fig_rank.update_traces(textposition="outside")
    st.plotly_chart(fig_rank, use_container_width=True)

st.markdown("### 🥇 Ranking dos Campi")
rank_campus = df_inst.groupby(["INSTITUICAO", "CAMPUS", "SG_UF_ESC"])["MEDIA"].mean().reset_index().sort_values("MEDIA", ascending=False)
fig_campus = px.bar(rank_campus.head(20), x="MEDIA", y="CAMPUS", orientation="h",
    color="MEDIA", color_continuous_scale="Greens",
    text=rank_campus.head(20)["MEDIA"].round(1).astype(str),
    hover_data={"INSTITUICAO": True, "SG_UF_ESC": True}, title="Top 20 Campi (média geral 2014-2025)")
fig_campus.update_layout(height=500, yaxis=dict(categoryorder="total ascending"), showlegend=False, margin=dict(l=0, r=0, t=50, b=0))
fig_campus.update_traces(textposition="outside")
st.plotly_chart(fig_campus, use_container_width=True)

st.markdown("### 📈 Série Temporal por Campus")
campus_list = sorted(df_inst["CAMPUS"].unique())
if campus_list:
    campus_sel = st.selectbox("🏛️ Selecione um campus", campus_list, key="campus_ts_if")
    df_c = df_inst[df_inst["CAMPUS"] == campus_sel].sort_values("ANO")
    fig_ts = go.Figure()
    fig_ts.add_trace(go.Scatter(x=df_c["ANO"], y=df_c["MEDIA"], mode="lines+markers",
        name=campus_sel, line=dict(color="#2ecc71", width=4), marker=dict(size=10)))
    fig_ts.add_trace(go.Scatter(x=nac_fed_br["ANO"], y=nac_fed_br["MEDIA"], mode="lines",
        name="Brasil (Federal)", line=dict(color="#e74c3c", width=2, dash="dash")))
    fig_ts.update_layout(title=f"{campus_sel} vs Brasil (Rede Federal)", height=400,
        hovermode="x unified", xaxis=dict(dtick=1), margin=dict(l=0, r=0, t=50, b=0))
    st.plotly_chart(fig_ts, use_container_width=True)

st.markdown("### 🗺️ Mapa dos Campi")
campi_map = campi_rede.copy()
# Agrega média do ENEM por (municipio, uf, instituicao)
media_campi = df_inst.groupby(["CAMPUS", "SG_UF_ESC", "INSTITUICAO"])["MEDIA"].mean().reset_index()
media_campi.columns = ["cidade_media", "uf", "instituicao", "MEDIA_ENEM"]
media_campi["cidade_norm"] = media_campi["cidade_media"].apply(util.normalizar_cidade)
# Normaliza chave de merge do mapa (usa municipio_merge quando disponível)
campi_map["merge_key"] = campi_map["municipio_merge"].where(
    campi_map["municipio_merge"].notna() & (campi_map["municipio_merge"] != ""),
    campi_map["municipio"]
)
campi_map["merge_norm"] = campi_map["merge_key"].apply(util.normalizar_cidade)
campi_map = campi_map.merge(
    media_campi,
    left_on=["merge_norm", "uf", "instituicao"],
    right_on=["cidade_norm", "uf", "instituicao"],
    how="left"
)
campi_map["MEDIA_ENEM"] = campi_map["MEDIA_ENEM"].round(1)

if inst_selecionado != "Todas":
    campi_map = campi_map[campi_map["instituicao"] == inst_selecionado]
if tipos_sel:
    campi_map = campi_map[campi_map["tipo_instituicao"].str.upper().isin([t.upper() for t in tipos_sel])]
campi_map = campi_map.dropna(subset=["latitude", "longitude"])
if not campi_map.empty:
    fig_map = px.scatter_mapbox(campi_map, lat="latitude", lon="longitude",
        hover_name="municipio",
        hover_data={"instituicao": True, "tipo_instituicao": True, "uf": True,
                     "MEDIA_ENEM": ":.1f", "latitude": False, "longitude": False},
        color="tipo_instituicao" if inst_selecionado == "Todas" else None,
        zoom=3, height=500, title="Distribuição Geográfica dos Campi",
        color_discrete_map={"IF": "#2ecc71", "CEFET": "#3498db", "CPII": "#f39c12",
                            "UTFPR": "#9b59b6", "ETV": "#e74c3c"})
    fig_map.update_layout(mapbox_style="carto-darkmatter", margin=dict(l=0, r=0, t=50, b=0))
    st.plotly_chart(fig_map, use_container_width=True)

st.markdown("---")
st.markdown("## 🔬 Perfil por Disciplina")
st.markdown("Em qual disciplina cada instituição/campus se destaca?")

disciplinas = ["LC", "CH", "CN", "MT", "RD"]
labels_disc = {"LC": "Linguagens", "CH": "Humanas", "CN": "Natureza", "MT": "Matemática", "RD": "Redação"}

c7, c8 = st.columns([1.5, 1])
with c7:
    if inst_selecionado == "Todas":
        radar_data = df_inst.groupby("INSTITUICAO")[disciplinas].mean().reset_index()
    else:
        radar_data = df_inst.groupby("CAMPUS")[disciplinas].mean().reset_index()
    if len(radar_data) <= 20:
        fig_radar = go.Figure()
        for _, row in radar_data.iterrows():
            vals = row[disciplinas].tolist() + [row[disciplinas].tolist()[0]]
            theta = [labels_disc[d] for d in disciplinas] + [labels_disc[disciplinas[0]]]
            fig_radar.add_trace(go.Scatterpolar(r=vals, theta=theta, name=row[radar_data.columns[0]], opacity=0.7, line=dict(width=2)))
        fig_radar.update_layout(title="Perfil por Disciplina", height=500,
            polar=dict(radialaxis=dict(visible=True, range=[450, 750])), margin=dict(l=80, r=80, t=50, b=0))
        st.plotly_chart(fig_radar, use_container_width=True)
    else:
        radar_data_plot = radar_data.set_index(radar_data.columns[0])
        fig_heat = px.imshow(radar_data_plot, text_auto=".0f", aspect="auto",
            color_continuous_scale="RdYlGn", title="Média por Disciplina",
            labels=dict(x="Disciplina", y=radar_data.columns[0], color="Média"))
        st.plotly_chart(fig_heat, use_container_width=True)

with c8:
    st.markdown('<div class="insight-green">', unsafe_allow_html=True)
    st.markdown("**  Disciplinas**")
    media_disc = df_inst[disciplinas].mean()
    melhor_disc = labels_disc[media_disc.idxmax()]
    pior_disc = labels_disc[media_disc.idxmin()]
    st.markdown(f"""Melhor desempenho: **{melhor_disc}** ({media_disc.max():.0f})<br>Maior desafio: **{pior_disc}** ({media_disc.min():.0f})""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    fig_disc_bar = px.bar(x=media_disc.values, y=[labels_disc[d] for d in media_disc.index],
        orientation="h", color=media_disc.values, color_continuous_scale="RdYlGn",
        text=media_disc.round(1).astype(str), labels={"x": "Média", "y": ""}, title="Média por Disciplina")
    fig_disc_bar.update_layout(height=350, showlegend=False, margin=dict(l=0, r=0, t=50, b=0))
    fig_disc_bar.update_traces(textposition="outside")
    st.plotly_chart(fig_disc_bar, use_container_width=True)

st.markdown("---")
st.markdown("## 🏫 Rede Federal vs Demais Redes nos Mesmos Municípios")
st.markdown("Como a rede federal se compara com Estadual, Municipal e Privada nas mesmas cidades?")

municipios_rede = df_rede_fed["NO_MUNICIPIO_ESC"].unique()
df_local = df[df["NO_MUNICIPIO_ESC"].isin(municipios_rede)]
comp_rede = df_local.groupby(["ANO", "DEPENDENCIA"])["MEDIA"].mean().reset_index()
fig_comp = go.Figure()
cores_rede_local = {"Federal": "#2ecc71", "Estadual": "#e74c3c", "Municipal": "#f39c12", "Privada": "#3498db"}
for rede in comp_rede["DEPENDENCIA"].unique():
    d = comp_rede[comp_rede["DEPENDENCIA"] == rede].sort_values("ANO")
    fig_comp.add_trace(go.Scatter(x=d["ANO"], y=d["MEDIA"], mode="lines+markers",
        name=rede, line=dict(width=3, color=cores_rede_local.get(rede, "#888")), marker=dict(size=8)))
fig_comp.add_trace(go.Scatter(x=nac_fed_br["ANO"], y=nac_fed_br["MEDIA"], mode="lines",
    name="Brasil (Federal)", line=dict(color="#888", width=2, dash="dash")))
fig_comp.update_layout(title="Comparação entre Redes nos Municípios com Presença Federal", height=450,
    hovermode="x unified", xaxis=dict(dtick=1), margin=dict(l=0, r=0, t=50, b=0))
st.plotly_chart(fig_comp, use_container_width=True)

st.markdown("### 🌍 Desempenho por Região")
reg_data = df_inst.groupby("REGIAO").agg(MEDIA=("MEDIA", "mean"), CAMPI=("CAMPUS", "nunique")).reset_index().sort_values("MEDIA", ascending=False)
fig_reg = px.bar(reg_data, x="MEDIA", y="REGIAO", orientation="h",
    color="MEDIA", color_continuous_scale="Greens",
    text=reg_data["MEDIA"].round(1).astype(str) + " (" + reg_data["CAMPI"].astype(str) + " campi)", title="Média por Região")
fig_reg.update_layout(height=350, yaxis=dict(categoryorder="total ascending"), showlegend=False, margin=dict(l=0, r=0, t=50, b=0))
fig_reg.update_traces(textposition="outside")
st.plotly_chart(fig_reg, use_container_width=True)

st.markdown("### 📈 Quem Mais Evoluiu?")
evol = df_inst.groupby(["CAMPUS", "ANO"]).agg(MEDIA=("MEDIA", "mean"), ALUNOS=("ALUNOS", "sum")).reset_index()
evol = evol[evol["ALUNOS"] >= 10]
evol_list = []
for campus, grp in evol.groupby("CAMPUS"):
    grp = grp.sort_values("ANO")
    if len(grp) >= 2:
        first, last = grp.iloc[0], grp.iloc[-1]
        evol_list.append({"CAMPUS": campus,
            "INSTITUICAO": df_inst[df_inst["CAMPUS"] == campus]["INSTITUICAO"].iloc[0],
            "PRIMEIRO_ANO": int(first["ANO"]), "ULTIMO_ANO": int(last["ANO"]),
            "MEDIA_INI": first["MEDIA"], "MEDIA_FIM": last["MEDIA"], "EVOLUCAO": last["MEDIA"] - first["MEDIA"]})
evol_df = pd.DataFrame(evol_list).sort_values("EVOLUCAO", ascending=False)
if not evol_df.empty:
    top_evol = evol_df.head(10)
    top_evol["ROTULO"] = top_evol.apply(lambda r: f"{r['EVOLUCAO']:.1f} ({r['PRIMEIRO_ANO']}→{r['ULTIMO_ANO']})", axis=1)
    fig_evol = px.bar(top_evol, x="EVOLUCAO", y="CAMPUS", orientation="h",
        color="EVOLUCAO", color_continuous_scale="Greens", text=top_evol["ROTULO"],
        hover_data={"INSTITUICAO": True}, title="Campi com Maior Evolução")
    fig_evol.update_layout(height=400, yaxis=dict(categoryorder="total ascending"), showlegend=False, margin=dict(l=0, r=0, t=50, b=0))
    fig_evol.update_traces(textposition="outside")
    st.plotly_chart(fig_evol, use_container_width=True)

st.markdown("---")
st.markdown("## 📋 Tabela Comparativa")
st.markdown("Todos os dados em uma tabela para análise detalhada.")

ano_tab = st.selectbox("📅 Ano", sorted(df["ANO"].unique()), key="ano_tab_if")
rede_tab = st.selectbox("🏫 Rede", ["Federal", "Estadual", "Municipal", "Privada"], key="rede_tab_if")

tab_filtro = df_rede[(df_rede["ANO"] == ano_tab) & (df_rede["DEPENDENCIA"] == rede_tab)]
if inst_selecionado != "Todas":
    tab_filtro = tab_filtro[tab_filtro["INSTITUICAO"] == inst_selecionado]
if tipos_sel:
    tab_filtro = tab_filtro[tab_filtro["TIPO_INSTITUICAO"].isin([t.upper() for t in tipos_sel])]

if not tab_filtro.empty:
    tab_filtro = tab_filtro.groupby(["INSTITUICAO", "TIPO_INSTITUICAO", "CAMPUS", "SG_UF_ESC"], as_index=False).agg(
        MEDIA=("MEDIA", "mean"), LC=("LC", "mean"), CH=("CH", "mean"),
        CN=("CN", "mean"), MT=("MT", "mean"), RD=("RD", "mean"), ESCOLAS=("MEDIA", "count"),
    ).sort_values("MEDIA", ascending=False)
    tab_show = tab_filtro[["INSTITUICAO", "TIPO_INSTITUICAO", "CAMPUS", "SG_UF_ESC", "MEDIA", "LC", "CH", "CN", "MT", "RD", "ESCOLAS"]].reset_index(drop=True)
    tab_show.columns = ["Instituição", "Tipo", "Campus", "UF", "Média", "LC", "CH", "CN", "MT", "RD", "Escolas"]
    st.dataframe(tab_show.style.format({"Média": "{:.2f}", "LC": "{:.1f}", "CH": "{:.1f}", "CN": "{:.1f}", "MT": "{:.1f}", "RD": "{:.1f}"}), use_container_width=True, height=400)
    csv = tab_show.to_csv(index=False, sep=";", decimal=",")
    st.download_button("Exportar CSV", data=csv, file_name=f"rede_federal_{ano_tab}_{rede_tab}.csv", mime="text/csv")
else:
    st.info(f"Nenhum dado disponível para {rede_tab} em {ano_tab} nos municípios com Rede Federal.", icon="ℹ️")

st.markdown("---")
st.markdown(f"""
<div style="text-align:center; color:#666; font-size:0.85rem; padding:1rem;">
    Dashboard Rede Federal no ENEM — Dados ENEM/INEP (2014–2025) | {datetime.now().strftime('%B %Y')}<br>
    {total_campi} campi analisados em {total_reg:,} registros da rede federal ao longo de 12 anos.<br>
    Desenvolvido por luciano.espiriao@ifmg.edu.br. 2026 - Todos os direitos reservados.
</div>
""", unsafe_allow_html=True)
