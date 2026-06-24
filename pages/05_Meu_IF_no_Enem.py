import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from dados_compartilhados import carregar_dados, carregar_rede_federal, preparar_dados_rede_federal
import util

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
    .inst-green { color: #2ecc71; font-weight: 700; }
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

st.sidebar.header("\U0001F50D Filtros")

tipos_disponiveis = sorted(df_rede_fed["TIPO_INSTITUICAO"].unique())
tipo_map = {"IF": "Institutos Federais", "CEFET": "CEFETs", "CPII": "Colégio Pedro II", "UTFPR": "UTFPR", "ETV": "Escolas Técnicas Vinculadas"}
tipo_sel = st.sidebar.selectbox("\U0001F3EB Tipo de Instituição", tipos_disponiveis,
    format_func=lambda x: tipo_map.get(x, x), key="meuif_tipo")

inst_disponiveis = sorted(df_rede_fed[df_rede_fed["TIPO_INSTITUICAO"] == tipo_sel]["INSTITUICAO"].unique())
inst_sel = st.sidebar.selectbox("\U0001F3DB️ Instituição", inst_disponiveis, key="meuif_inst")

df_inst = df_rede_fed[df_rede_fed["INSTITUICAO"] == inst_sel].copy()
campus_list = sorted(df_inst["CAMPUS"].unique())

palette = px.colors.qualitative.Plotly + px.colors.qualitative.Set2 + px.colors.qualitative.Set1
cor_campus = {c: palette[i % len(palette)] for i, c in enumerate(campus_list)}
cor_campus_norm = {util.normalizar_cidade(k): v for k, v in cor_campus.items()}

# Agregações base
nac = df.groupby("ANO").agg(MEDIA=("MEDIA", "mean")).reset_index()
nac.columns = ["ANO", "MEDIA_BR"]
nac["REDE"] = "Brasil"

nac_rede = df.groupby(["ANO", "DEPENDENCIA"]).agg(MEDIA=("MEDIA", "mean")).reset_index()
nac_rede.columns = ["ANO", "REDE", "MEDIA_BR"]

uf_inst = df_inst["SG_UF_ESC"].unique()
uf_data = df[(df["SG_UF_ESC"].isin(uf_inst)) & (df["DEPENDENCIA"] == "Federal")].groupby(["ANO", "SG_UF_ESC"]).agg(MEDIA=("MEDIA", "mean")).reset_index()
uf_data.columns = ["ANO", "UF", "MEDIA_UF"]

media_uf_fed = df[(df["SG_UF_ESC"].isin(uf_inst)) & (df["DEPENDENCIA"] == "Federal")]["MEDIA"].mean()

inst_campus = df_inst.groupby(["ANO", "CAMPUS", "SG_UF_ESC"]).agg(
    MEDIA=("MEDIA", "mean"), LC=("LC", "mean"), CH=("CH", "mean"),
    CN=("CN", "mean"), MT=("MT", "mean"), RD=("RD", "mean"),
    ESCOLAS=("MEDIA", "count"), ALUNOS=("ALUNOS", "sum"),
).reset_index()

inst_geral = df_inst.groupby(["ANO"]).agg(
    MEDIA=("MEDIA", "mean"), ESCOLAS=("MEDIA", "count"),
).reset_index()

uf_agg = uf_data.groupby("ANO")["MEDIA_UF"].mean().reset_index()
uf_agg.columns = ["ANO", "MEDIA_UF"]

# Tabela comparativa
comp = inst_campus.merge(uf_agg, on=["ANO"], how="left")
comp = comp.merge(nac_rede[nac_rede["REDE"] == "Federal"][["ANO", "MEDIA_BR"]], on=["ANO"], how="left")
comp["DIF_UF"] = comp["MEDIA"] - comp["MEDIA_UF"]
comp["DIF_BR"] = comp["MEDIA"] - comp["MEDIA_BR"]

# ─── KPIs ───
media_inst = df_inst["MEDIA"].mean()
media_br_federal = df[df["DEPENDENCIA"] == "Federal"]["MEDIA"].mean()
melhor_campus = df_inst.groupby("CAMPUS")["MEDIA"].mean().idxmax()
total_reg = len(df_inst)
sigla_ufs = ", ".join(sorted(uf_inst))

c_logo, c_titulo = st.columns([1, 5])
with c_logo:
    st.markdown("<h1 style='font-size:3rem; margin:0;'></h1>", unsafe_allow_html=True)
with c_titulo:
    st.markdown(f"<p class='title'>  {inst_sel} no ENEM</p>", unsafe_allow_html=True)
    st.markdown(f"<p class='subtitle'>A trajetória do {tipo_map.get(tipo_sel, tipo_sel)} no ENEM 2014–2025 — desempenho, evolução e comparação com o Brasil</p>", unsafe_allow_html=True)

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value inst-green">{media_inst:.1f}</div>
        <div class="kpi-label">Média ({tipo_map.get(tipo_sel, tipo_sel)})</div>
    </div>""", unsafe_allow_html=True)
with k2:
    diff_uf = media_inst - media_uf_fed
    cor_uf = "#2ecc71" if diff_uf > 0 else "#e74c3c"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value" style="color:{cor_uf}">{diff_uf:+.1f}</div>
        <div class="kpi-label">vs Rede Federal ({sigla_ufs})</div>
    </div>""", unsafe_allow_html=True)
with k3:
    diff_br = media_inst - media_br_federal
    cor_br = "#2ecc71" if diff_br > 0 else "#e74c3c"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value" style="color:{cor_br}">{diff_br:+.1f}</div>
        <div class="kpi-label">vs Brasil Federal</div>
    </div>""", unsafe_allow_html=True)
with k4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value" style="color:#f39c12">{str(melhor_campus)[:12]}...</div>
        <div class="kpi-label">Maior média</div>
    </div>""", unsafe_allow_html=True)
with k5:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value">{total_reg:,}</div>
        <div class="kpi-label">Registros (Federal)</div>
    </div>""", unsafe_allow_html=True)

st.markdown("---")

# ─── CAPÍTULO 1: PANORAMA ───
st.markdown(f"\U0001F30D Capítulo 1: {inst_sel} no Contexto Nacional")
st.markdown(f"Como {inst_sel} se posiciona frente ao Brasil e aos estados onde atua?")

c1, c2 = st.columns([2, 1])

with c1:
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=nac["ANO"], y=nac["MEDIA_BR"], mode="lines+markers",
        name="Brasil (todas as redes)", line=dict(color="#888", width=2, dash="dash"),
        marker=dict(size=6), hovertemplate="%{x}: %{y:.1f}<extra></extra>",
    ))
    fig1.add_trace(go.Scatter(
        x=nac_rede[nac_rede["REDE"] == "Federal"]["ANO"],
        y=nac_rede[nac_rede["REDE"] == "Federal"]["MEDIA_BR"],
        mode="lines+markers", name="Brasil (Rede Federal)",
        line=dict(color="#e74c3c", width=2, dash="dot"), marker=dict(size=6),
    ))
    for uf in sorted(uf_inst):
        d_uf = uf_data[uf_data["UF"] == uf].sort_values("ANO")
        if not d_uf.empty:
            fig1.add_trace(go.Scatter(
                x=d_uf["ANO"], y=d_uf["MEDIA_UF"], mode="lines+markers",
                name=f"{uf} (Federal)", line=dict(width=2), marker=dict(size=6),
            ))
    fig1.add_trace(go.Scatter(
        x=inst_geral["ANO"], y=inst_geral["MEDIA"],
        mode="lines+markers", name=inst_sel,
        line=dict(color="#2ecc71", width=4), marker=dict(size=10),
    ))
    fig1.update_layout(title=f"Evolução da Média: {inst_sel} vs Brasil vs Estados (Rede Federal)", height=450,
                       hovermode="x unified", xaxis=dict(dtick=1),
                       margin=dict(l=0, r=0, t=50, b=0))
    st.plotly_chart(fig1, use_container_width=True)

with c2:
    st.markdown('<div class="insight-box">', unsafe_allow_html=True)
    st.markdown("**  Desempenho**")
    st.markdown(f"""
    {inst_sel} {'supera' if diff_br >= 0 else 'fica abaixo da'} média da rede federal brasileira em **{abs(diff_br):.1f} pontos**{'.' if diff_br >= 0 else ', e abaixo.'}
    """)
    if len(uf_inst) > 0:
        st.markdown(f"vs rede federal {'/'.join(sorted(uf_inst))}: **{diff_uf:+.1f} pontos**")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="insight-box">', unsafe_allow_html=True)
    st.markdown("**  Crescimento consistente**")
    fed_evol = inst_geral.set_index("ANO")["MEDIA"]
    ano_ini = int(fed_evol.first_valid_index())
    ano_fim = int(fed_evol.last_valid_index())
    med_ini = fed_evol.loc[ano_ini]
    med_fim = fed_evol.loc[ano_fim]
    st.markdown(f"""
    A média subiu de **{med_ini:.0f}** ({ano_ini}) 
    para **{med_fim:.0f}** ({ano_fim}) — 
    um crescimento de **{med_fim - med_ini:.0f} pontos**.
    """)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")

# ─── CAPÍTULO 2: RANKING DOS CAMPI ───
st.markdown("\U0001F947 Capítulo 2: O Ranking dos Campi")
st.markdown("Qual campus lidera? Qual mais evoluiu? Como se comparam entre si?")

c3, c4 = st.columns(2)

with c3:
    rank_campus = df_inst.groupby("CAMPUS")["MEDIA"].mean().sort_values(ascending=False).reset_index()
    rank_campus.columns = ["CAMPUS", "MEDIA"]
    rank_campus["COR"] = rank_campus["CAMPUS"].apply(lambda x: cor_campus_norm.get(util.normalizar_cidade(x), "#888"))

    fig_rank = px.bar(rank_campus, x="MEDIA", y="CAMPUS", orientation="h",
                      color="MEDIA", color_continuous_scale="Greens",
                      text=rank_campus["MEDIA"].round(1).astype(str),
                      title=f"Ranking dos Campi {inst_sel} (média geral 2014-2025)")
    fig_rank.update_layout(height=500, yaxis=dict(categoryorder="total ascending"),
                           showlegend=False, margin=dict(l=0, r=0, t=50, b=0))
    fig_rank.update_traces(textposition="outside")
    st.plotly_chart(fig_rank, use_container_width=True)

with c4:
    st.markdown("### \U0001F4C8 Série Temporal por Campus")
    campus_sel = st.selectbox("\U0001F3DB️ Selecione um campus", campus_list, key="meuif_campus_ts")
    df_c = df_inst[df_inst["CAMPUS"] == campus_sel].sort_values("ANO")
    df_c_br = nac_rede[nac_rede["REDE"] == "Federal"].copy()
    df_c_uf = uf_data.groupby("ANO")["MEDIA_UF"].mean().reset_index()

    fig_ts = go.Figure()
    fig_ts.add_trace(go.Scatter(x=df_c["ANO"], y=df_c["MEDIA"], mode="lines+markers",
                                name=campus_sel, line=dict(color=cor_campus_norm.get(util.normalizar_cidade(campus_sel), "#2ecc71"), width=4),
                                marker=dict(size=10), hovertemplate="%{x}: %{y:.1f}<extra></extra>"))
    fig_ts.add_trace(go.Scatter(x=df_c_br["ANO"], y=df_c_br["MEDIA_BR"], mode="lines",
                                name="Brasil (Federal)", line=dict(color="#e74c3c", width=2, dash="dash")))
    if not df_c_uf.empty:
        fig_ts.add_trace(go.Scatter(x=df_c_uf["ANO"], y=df_c_uf["MEDIA_UF"], mode="lines",
                                    name=f"Média UFs ({sigla_ufs})", line=dict(color="#3498db", width=2, dash="dot")))
    fig_ts.update_layout(title=f"{campus_sel} vs Brasil e UFs (Rede Federal)", height=400,
                         hovermode="x unified", xaxis=dict(dtick=1),
                         margin=dict(l=0, r=0, t=50, b=0))
    st.plotly_chart(fig_ts, use_container_width=True)

# Gap chart
st.markdown("### \U0001F4CA Diferença em relação ao Brasil e UFs (por campus)")

comp_fed = comp.groupby("CAMPUS")[["MEDIA", "MEDIA_BR", "MEDIA_UF"]].mean().reset_index()
comp_fed["DIF_BR"] = comp_fed["MEDIA"] - comp_fed["MEDIA_BR"]
comp_fed["DIF_UF"] = comp_fed["MEDIA"] - comp_fed["MEDIA_UF"]
comp_fed = comp_fed.sort_values("DIF_BR", ascending=False)

fig_gap = go.Figure()
fig_gap.add_trace(go.Bar(
    name="vs Brasil (Federal)", x=comp_fed["CAMPUS"], y=comp_fed["DIF_BR"],
    marker_color="#2ecc71", hovertemplate="%{x}: %{y:+.1f}<extra></extra>",
))
fig_gap.add_trace(go.Bar(
    name=f"vs UFs ({sigla_ufs})", x=comp_fed["CAMPUS"], y=comp_fed["DIF_UF"],
    marker_color="#3498db", hovertemplate="%{x}: %{y:+.1f}<extra></extra>",
))
fig_gap.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.3)
fig_gap.update_layout(title="Quanto cada campus supera (ou fica abaixo) da média", height=400,
                      barmode="group", xaxis_tickangle=-45,
                      margin=dict(l=0, r=0, t=50, b=0))
st.plotly_chart(fig_gap, use_container_width=True)

st.markdown("---")

# ─── CAPÍTULO 3: EVOLUÇÃO DOS CAMPI ───
st.markdown("\U0001F4C8 Capítulo 3: Quem Mais Evoluiu?")
st.markdown("A trajetória individual de cada campus ao longo da década.")

c5, c6 = st.columns(2)

with c5:
    evol_data = df_inst.groupby(["CAMPUS", "ANO"]).agg(
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

# Bump chart
st.markdown("### \U0001F3C1 Corrida dos Campi: Ranking Ano a Ano")

rank_ano = df_inst.groupby(["ANO", "CAMPUS"])["MEDIA"].mean().reset_index()
rank_ano["RANK"] = rank_ano.groupby("ANO")["MEDIA"].rank(ascending=False)

fig_bump = go.Figure()
for camp in sorted(rank_ano["CAMPUS"].unique()):
    d = rank_ano[rank_ano["CAMPUS"] == camp].sort_values("ANO")
    fig_bump.add_trace(go.Scatter(
        x=d["ANO"], y=d["RANK"], mode="lines+markers", name=camp,
        line=dict(width=3, color=cor_campus_norm.get(util.normalizar_cidade(camp), "#888")),
        marker=dict(size=8), text=d["RANK"].astype(int), textposition="middle right",
        hovertemplate="%{x}: %{y:.0f}º<extra></extra>",
    ))
fig_bump.update_layout(title=f"Posição no Ranking Interno — {inst_sel}", height=450,
                       yaxis=dict(autorange="reversed", dtick=1, title="Posição"),
                       xaxis=dict(dtick=1), hovermode="x unified",
                       margin=dict(l=0, r=0, t=50, b=0))
st.plotly_chart(fig_bump, use_container_width=True)

st.markdown("---")

# ─── CAPÍTULO 4: PERFIL POR DISCIPLINA ───
st.markdown("\U0001F52C Capítulo 4: O Perfil de Cada Campus")
st.markdown("Em qual disciplina cada campus se destaca? Como é o perfil geral?")

disciplinas = ["LC", "CH", "CN", "MT", "RD"]
labels_disc = {"LC": "Linguagens", "CH": "Humanas", "CN": "Natureza", "MT": "Matemática", "RD": "Redação"}

c7, c8 = st.columns([1.5, 1])

with c7:
    radar_data = df_inst.groupby("CAMPUS")[disciplinas].mean().reset_index()
    fig_radar = go.Figure()
    for _, row in radar_data.iterrows():
        vals = row[disciplinas].tolist() + [row[disciplinas].tolist()[0]]
        theta = [labels_disc[d] for d in disciplinas] + [labels_disc[disciplinas[0]]]
        fig_radar.add_trace(go.Scatterpolar(
            r=vals, theta=theta, name=row["CAMPUS"],
            line=dict(width=2, color=cor_campus_norm.get(util.normalizar_cidade(row["CAMPUS"]), "#888")),
            opacity=0.7,
        ))
    fig_radar.update_layout(title="Perfil por Disciplina — Todos os Campi", height=500,
                            polar=dict(radialaxis=dict(visible=True, range=[450, 750])),
                            margin=dict(l=80, r=80, t=50, b=0))
    st.plotly_chart(fig_radar, use_container_width=True)

with c8:
    campus_radar = st.selectbox("\U0001F3AF Campus para destaque", campus_list, key="meuif_campus_radar")
    df_cr = radar_data[radar_data["CAMPUS"] == campus_radar]
    if not df_cr.empty:
        vals = df_cr[disciplinas].iloc[0].tolist()
        theta = [labels_disc[d] for d in disciplinas]

        fig_single = go.Figure()
        fig_single.add_trace(go.Scatterpolar(
            r=vals + [vals[0]], theta=theta + [theta[0]],
            name=campus_radar, fill="toself",
            line=dict(width=3, color=cor_campus_norm.get(util.normalizar_cidade(campus_radar), "#2ecc71")),
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
        st.markdown("**  Destaque**")
        st.markdown(f"""
        {campus_radar} tem seu melhor desempenho em **{melhor_disc_nome}** 
        e maior desafio em **{pior_disc_nome}**.
        """)
    st.markdown("</div>", unsafe_allow_html=True)

# Dispersão
st.markdown("### \u270D\ufe0f Matemática vs Redação: O Diferencial")

ano_disp = st.selectbox("\U0001F4C5 Ano", sorted(df["ANO"].unique()), key="meuif_ano_disp")
df_disp = df_inst[df_inst["ANO"] == ano_disp].groupby(
    "CAMPUS"
).agg(MT=("MT", "mean"), RD=("RD", "mean"), MEDIA=("MEDIA", "mean"), ESCOLAS=("MEDIA", "count")).reset_index()

if not df_disp.empty:
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

# ─── CAPÍTULO 5: Vs REDES LOCAIS ───
st.markdown("\u2694\ufe0f Capítulo 5: {inst_sel} vs as Demais Redes nos Mesmos Municípios")
st.markdown("Como a rede federal se compara com as redes Estadual, Municipal e Privada nas mesmas cidades?")

campus_comp = st.selectbox("\U0001F3DB️ Campus", campus_list, key="meuif_campus_comp")
municipio_campus = df_inst[df_inst["CAMPUS"] == campus_comp]["NO_MUNICIPIO_ESC"].iloc[0]
df_local = df[df["NO_MUNICIPIO_ESC"] == municipio_campus]
df_cc = df_local.groupby(["ANO", "DEPENDENCIA"])["MEDIA"].mean().reset_index()

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
fig_comp.update_layout(title=f"Comparação entre Redes — {campus_comp} ({municipio_campus})", height=450,
                       hovermode="x unified", xaxis=dict(dtick=1),
                       margin=dict(l=0, r=0, t=50, b=0))
st.plotly_chart(fig_comp, use_container_width=True)

# Heatmap
st.markdown("### \U0001F4CB Matriz: Média por Campus e Rede (todos os anos)")

matriz = df_inst.groupby(["CAMPUS", "DEPENDENCIA"])["MEDIA"].mean().reset_index()
heat = matriz.pivot(index="CAMPUS", columns="DEPENDENCIA", values="MEDIA")
if not heat.empty:
    fig_heat = px.imshow(heat, text_auto=".0f", aspect="auto",
                         color_continuous_scale="RdYlGn",
                         title="Média por Campus e Rede de Ensino",
                         labels=dict(x="Rede", y="Campus", color="Média"))
    fig_heat.update_layout(height=500, margin=dict(l=0, r=0, t=50, b=0))
    st.plotly_chart(fig_heat, use_container_width=True)

st.markdown("---")

# ─── CAPÍTULO 6: TABELA COMPARATIVA ───
st.markdown("\U0001F4CB Capítulo 6: Tabela Comparativa")
st.markdown("Todos os dados em uma tabela para análise detalhada.")

ano_tab = st.selectbox("\U0001F4C5 Ano", sorted(df["ANO"].unique()), key="meuif_ano_tab")
rede_tab = st.selectbox("\U0001F3EB Rede", ["Federal", "Estadual", "Municipal", "Privada"], key="meuif_rede_tab")

tab_filtro = comp[comp["ANO"] == ano_tab].copy()
tab_filtro = tab_filtro.sort_values("MEDIA", ascending=False)

if not tab_filtro.empty:
    cols_disp = [c for c in ["CAMPUS", "MEDIA", "MEDIA_UF", "MEDIA_BR", "DIF_UF", "DIF_BR", "LC", "CH", "CN", "MT", "RD", "ESCOLAS"] if c in tab_filtro.columns]
    tab_show = tab_filtro[cols_disp].reset_index(drop=True)
    tab_show.columns = ["Campus", "Média", "Média UFs", "Média Brasil", "Dif. vs UFs", "Dif. vs BR",
                        "LC", "CH", "CN", "MT", "RD", "Escolas"][:len(cols_disp)]
    fmt = {"Média": "{:.2f}", "Média UFs": "{:.2f}", "Média Brasil": "{:.2f}",
           "Dif. vs UFs": "{:+.2f}", "Dif. vs BR": "{:+.2f}",
           "LC": "{:.1f}", "CH": "{:.1f}", "CN": "{:.1f}", "MT": "{:.1f}", "RD": "{:.1f}",}
    fmt = {k: v for k, v in fmt.items() if k in tab_show.columns}
    st.dataframe(
        tab_show.style.format(fmt),
        use_container_width=True, height=400,
    )
    csv = tab_show.to_csv(index=False, sep=";", decimal=",")
    st.download_button("Exportar CSV", data=csv, file_name=f"{inst_sel.replace(' ', '_').replace('/', '_')}_{ano_tab}_{rede_tab}.csv", mime="text/csv")

st.markdown("---")
st.markdown(f"""
<div style="text-align:center; color:#666; font-size:0.85rem; padding:1rem;">
    Dashboard {inst_sel} no ENEM — Dados ENEM/INEP (2014–2025) | {datetime.now().strftime('%B %Y')}<br>
    {len(campus_list)} campi analisados em {total_reg:,} registros ao longo de 12 anos.
    https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem.<br>
    Desenvolvido por luciano.espiriao@ifmg.edu.br. 2026 - Todos os direitos reservados.    
</div>
""", unsafe_allow_html=True)
