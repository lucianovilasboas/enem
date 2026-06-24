import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from dados_compartilhados import carregar_dados, carregar_rede_federal
import util

st.markdown("""
<style>
    .title { font-size: 3rem; font-weight: 800; letter-spacing: -1px; margin-bottom: 0; }
    .subtitle { font-size: 1.1rem; color: #888; margin-top: 0; }
    .inst-card { background: #0e1117; border: 1px solid #333; border-radius: 12px; padding: 1.2rem 1.5rem; }
    .inst-label { font-size: 0.8rem; color: #888; text-transform: uppercase; letter-spacing: 1px; }
    .inst-value { font-size: 1.6rem; font-weight: 700; }
    .campus-row { background: #0e1117; border: 1px solid #2a2a2a; border-radius: 8px; padding: 0.8rem 1.2rem; margin: 0.3rem 0; }
    .campus-row:hover { border-color: #4ecdc4; }
    .campus-city { font-size: 1.1rem; font-weight: 600; }
    .campus-meta { font-size: 0.85rem; color: #888; }
    .tag { display: inline-block; background: #1a3a2e; color: #2ecc71; border-radius: 4px; padding: 0.1rem 0.5rem; font-size: 0.75rem; font-weight: 600; margin-right: 0.3rem; }
    .tag-if { background: #1a3a2e; color: #2ecc71; }
    .tag-cefet { background: #1a2a3e; color: #3498db; }
    .tag-cpii { background: #3e2a1a; color: #f39c12; }
    .tag-utfpr { background: #2e1a3e; color: #9b59b6; }
    .tag-etv { background: #3e1a1a; color: #e74c3c; }
    h2 { margin-top: 0.5rem; }
</style>
""", unsafe_allow_html=True)

tipo_map = {"IF": "Institutos Federais", "CEFET": "CEFETs", "CPII": "Colégio Pedro II", "UTFPR": "UTFPR", "ETV": "Escolas Técnicas Vinculadas"}
tag_class = {"IF": "tag-if", "CEFET": "tag-cefet", "CPII": "tag-cpii", "UTFPR": "tag-utfpr", "ETV": "tag-etv"}

with st.spinner("Carregando dados..."):
    campi_rede = carregar_rede_federal()
    df = carregar_dados()
    df_rede_enem = util.normalizar_dataframe(df.copy())
    # Merge ENEM data with campus registry
    campi_rede["_merge_norm"] = campi_rede.apply(
        lambda r: util.normalizar_cidade(r["municipio_merge"] if pd.notna(r["municipio_merge"]) and r["municipio_merge"] != "" else r["municipio"]),
        axis=1
    )
    df_rede_enem["_merge_norm"] = df_rede_enem["NO_MUNICIPIO_ESC"].apply(util.normalizar_cidade)
    df_rede_enem["uf"] = df_rede_enem["SG_UF_ESC"]
    merge_cols = ["_merge_norm", "uf"]
    enem_agg = df_rede_enem.merge(
        campi_rede[merge_cols + ["instituicao"]].drop_duplicates(subset=merge_cols),
        on=merge_cols, how="inner"
    ).groupby(["instituicao", "_merge_norm", "uf"]).agg(
        MEDIA=("MEDIA", "mean"), LC=("LC", "mean"), CH=("CH", "mean"),
        CN=("CN", "mean"), MT=("MT", "mean"), RD=("RD", "mean"),
        ESCOLAS=("MEDIA", "count"), ALUNOS=("ALUNOS", "sum"),
    ).reset_index()

df_reg = campi_rede.copy()
df_reg.columns = df_reg.columns.str.strip()
df_reg["municipio_exib"] = df_reg.apply(
    lambda r: r["municipio_merge"] if pd.notna(r["municipio_merge"]) and r["municipio_merge"] != "" else r["municipio"],
    axis=1
)

st.markdown('<p class="title">  Instituições da Rede Federal</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Cadastro completo dos Institutos Federais, CEFETs, UTFPR, Colégio Pedro II e Escolas Técnicas Vinculadas — localização, campi e desempenho no ENEM.</p>', unsafe_allow_html=True)

st.sidebar.header("\U0001F50D Filtros")

tipos_sel = st.sidebar.multiselect(
    "\U0001F3EB Tipo de Instituição",
    ["IF", "CEFET", "CPII", "UTFPR", "ETV"],
    format_func=lambda x: tipo_map.get(x, x),
    default=["IF", "CEFET", "CPII", "UTFPR", "ETV"],
    key="reg_tipo"
)

df_filtrado = df_reg[df_reg["tipo_instituicao"].isin(tipos_sel)]

# Agregações por instituição
agg_inst = df_filtrado.groupby(["instituicao", "tipo_instituicao"]).agg(
    CAMPI=("municipio", "nunique"),
    UFS=("uf", lambda x: ", ".join(sorted(x.unique()))),
    LAT=("latitude", "mean"),
    LON=("longitude", "mean"),
).reset_index().sort_values(["tipo_instituicao", "instituicao"])

# Merge ENEM data
enem_inst = enem_agg.groupby("instituicao").agg(
    MEDIA_ENEM=("MEDIA", "mean"),
    TOTAL_ESCOLAS=("ESCOLAS", "sum"),
).reset_index()
agg_inst = agg_inst.merge(enem_inst, on="instituicao", how="left")

st.markdown("---")

# ─── MAPA GERAL ───
st.markdown("\U0001F30D Mapa da Rede Federal")
st.markdown("Distribuição geográfica de todos os campi da rede federal de educação.")

fig_map = px.scatter_mapbox(
    df_filtrado,
    lat="latitude", lon="longitude",
    hover_name="municipio_exib",
    hover_data={
        "instituicao": True, "tipo_instituicao": True,
        "uf": True, "latitude": False, "longitude": False,
        "municipio_exib": False, "municipio": False, "municipio_merge": False,
    },
    color="tipo_instituicao",
    color_discrete_map={"IF": "#2ecc71", "CEFET": "#3498db", "CPII": "#f39c12", "UTFPR": "#9b59b6", "ETV": "#e74c3c"},
    zoom=3, height=500, title="Campi da Rede Federal de Educação",
)
fig_map.update_layout(mapbox_style="carto-darkmatter", margin=dict(l=0, r=0, t=50, b=0))
st.plotly_chart(fig_map, use_container_width=True)

st.markdown("---")

# ─── INSTITUIÇÃO ───
st.markdown("\U0001F3DB️ Instituições")

inst_sel = st.selectbox(
    "Selecione uma instituição para detalhes",
    agg_inst.apply(lambda r: f"{r['instituicao']} ({tipo_map.get(r['tipo_instituicao'], r['tipo_instituicao'])})", axis=1).tolist(),
    key="reg_inst_sel"
)
inst_nome = inst_sel.split(" (")[0]
inst_row = agg_inst[agg_inst["instituicao"] == inst_nome].iloc[0]

campi_inst = df_filtrado[df_filtrado["instituicao"] == inst_nome].copy()
enem_inst_detalhe = enem_agg[enem_agg["instituicao"] == inst_nome].copy()

# Card da instituição
col_info = st.columns([1, 1, 1, 1, 1])
with col_info[0]:
    tipo = inst_row["tipo_instituicao"]
    cor_tag = {"IF": "#2ecc71", "CEFET": "#3498db", "CPII": "#f39c12", "UTFPR": "#9b59b6", "ETV": "#e74c3c"}.get(tipo, "#888")
    st.markdown(f"""
    <div class="inst-card">
        <div class="inst-label">Tipo</div>
        <div class="inst-value" style="color:{cor_tag}">{tipo_map.get(tipo, tipo)}</div>
    </div>""", unsafe_allow_html=True)
with col_info[1]:
    st.markdown(f"""
    <div class="inst-card">
        <div class="inst-label">Campi</div>
        <div class="inst-value">{int(inst_row['CAMPI'])}</div>
    </div>""", unsafe_allow_html=True)
with col_info[2]:
    st.markdown(f"""
    <div class="inst-card">
        <div class="inst-label">Estados</div>
        <div class="inst-value" style="font-size:1rem;">{inst_row['UFS']}</div>
    </div>""", unsafe_allow_html=True)
with col_info[3]:
    media_val = inst_row.get("MEDIA_ENEM", None)
    if pd.notna(media_val):
        st.markdown(f"""
        <div class="inst-card">
            <div class="inst-label">Média ENEM</div>
            <div class="inst-value" style="color:#2ecc71">{media_val:.1f}</div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="inst-card">
            <div class="inst-label">Média ENEM</div>
            <div class="inst-value" style="color:#666">—</div>
        </div>""", unsafe_allow_html=True)
with col_info[4]:
    escolas_val = inst_row.get("TOTAL_ESCOLAS", None)
    if pd.notna(escolas_val):
        st.markdown(f"""
        <div class="inst-card">
            <div class="inst-label">Escolas no ENEM</div>
            <div class="inst-value">{int(escolas_val):,}</div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="inst-card">
            <div class="inst-label">Escolas no ENEM</div>
            <div class="inst-value" style="color:#666">—</div>
        </div>""", unsafe_allow_html=True)

st.markdown("---")
st.markdown(f"### \U0001F4CD Campi — {inst_nome}")

# Mapa focado na instituição
fig_inst_map = px.scatter_mapbox(
    campi_inst,
    lat="latitude", lon="longitude",
    hover_name="municipio_exib",
    hover_data={"uf": True, "latitude": False, "longitude": False},
    zoom=5, height=400,
    title=f"Campi — {inst_nome}",
)
fig_inst_map.update_layout(mapbox_style="carto-darkmatter", margin=dict(l=0, r=0, t=50, b=0))
st.plotly_chart(fig_inst_map, use_container_width=True)

# Lista de campi
campi_inst_sorted = campi_inst.sort_values(["uf", "municipio_exib"])
enem_lookup = enem_inst_detalhe.set_index(["_merge_norm", "uf"])

for _, row in campi_inst_sorted.iterrows():
    cidade = row["municipio_exib"]
    uf = row["uf"]
    lat, lon = row["latitude"], row["longitude"]
    maps_url = f"https://www.google.com/maps?q={lat},{lon}"
    osm_url = f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}&zoom=14"

    enem_key = (util.normalizar_cidade(cidade), uf)
    enem_info = enem_lookup.loc[enem_key] if enem_key in enem_lookup.index else None

    media_str = f"Média ENEM: **{enem_info['MEDIA']:.1f}**" if enem_info is not None else ""

    st.markdown(f"""
    <div class="campus-row">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <span class="campus-city">{cidade}</span>
                <span class="tag {tag_class.get(tipo, 'tag-if')}">{tipo_map.get(tipo, tipo)}</span>
                <span class="campus-meta"> {uf}</span>
                <br>
                <span class="campus-meta">📍 {lat:.4f}, {lon:.4f}</span>
                <span class="campus-meta"> | </span>
                <a href="{maps_url}" target="_blank" style="color:#4ecdc4; text-decoration:none;">Google Maps</a>
                <span class="campus-meta"> · </span>
                <a href="{osm_url}" target="_blank" style="color:#3498db; text-decoration:none;">OpenStreetMap</a>
                {' | ' + media_str if media_str else ''}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ─── RESUMO: Todas as Instituições ───
st.markdown("\U0001F4CA Resumo das Instituições")

tipo_filtro_resumo = st.selectbox(
    "\U0001F3EB Filtrar por tipo",
    ["Todos"] + [tipo_map.get(t, t) for t in tipos_sel],
    key="reg_tipo_resumo"
)

if tipo_filtro_resumo != "Todos":
    tipo_key = {v: k for k, v in tipo_map.items()}.get(tipo_filtro_resumo, tipo_filtro_resumo)
    df_resumo = agg_inst[agg_inst["tipo_instituicao"] == tipo_key]
else:
    df_resumo = agg_inst

df_show = df_resumo[["instituicao", "tipo_instituicao", "CAMPI", "UFS", "MEDIA_ENEM", "TOTAL_ESCOLAS"]].copy()
df_show.columns = ["Instituição", "Tipo", "Campi", "UFs", "Média ENEM", "Escolas (ENEM)"]
df_show["Tipo"] = df_show["Tipo"].map(tipo_map)
df_show["Média ENEM"] = df_show["Média ENEM"].round(1)

st.dataframe(
    df_show.style.format({"Média ENEM": "{:.1f}", "Escolas (ENEM)": "{:,.0f}"}),
    use_container_width=True, height=400,
)

csv = df_show.to_csv(index=False, sep=";", decimal=",")
st.download_button("Exportar CSV", data=csv, file_name="instituicoes_rede_federal.csv", mime="text/csv")

st.markdown("---")

# ─── ESTATÍSTICAS ───
st.markdown("\U0001F4CA Estatísticas da Rede")

col_est1, col_est2, col_est3, col_est4 = st.columns(4)
with col_est1:
    st.markdown(f"""<div class="inst-card"><div class="inst-label">Instituições</div><div class="inst-value" style="color:#2ecc71">{df_reg['instituicao'].nunique()}</div></div>""", unsafe_allow_html=True)
with col_est2:
    st.markdown(f"""<div class="inst-card"><div class="inst-label">Campi Mapeados</div><div class="inst-value" style="color:#3498db">{len(df_reg):,}</div></div>""", unsafe_allow_html=True)
with col_est3:
    st.markdown(f"""<div class="inst-card"><div class="inst-label">Municípios</div><div class="inst-value" style="color:#f39c12">{df_reg['municipio'].nunique()}</div></div>""", unsafe_allow_html=True)
with col_est4:
    st.markdown(f"""<div class="inst-card"><div class="inst-label">Estados</div><div class="inst-value" style="color:#e94560">{df_reg['uf'].nunique()}</div></div>""", unsafe_allow_html=True)

# Gráfico: Campi por tipo
tipo_counts = df_reg["tipo_instituicao"].value_counts().reset_index()
tipo_counts.columns = ["Tipo", "Campi"]
tipo_counts["Tipo"] = tipo_counts["Tipo"].map(tipo_map)
fig_tipo = px.bar(tipo_counts, x="Tipo", y="Campi", color="Tipo",
    color_discrete_map={"Institutos Federais": "#2ecc71", "CEFETs": "#3498db",
                        "Colégio Pedro II": "#f39c12", "UTFPR": "#9b59b6", "Escolas Técnicas Vinculadas": "#e74c3c"},
    text="Campi", title="Campi por Tipo de Instituição")
fig_tipo.update_layout(showlegend=False, height=400, margin=dict(l=0, r=0, t=50, b=0))
fig_tipo.update_traces(textposition="outside")
st.plotly_chart(fig_tipo, use_container_width=True)

# Top estados
top_uf = df_reg["uf"].value_counts().head(15).reset_index()
top_uf.columns = ["UF", "Campi"]
fig_uf = px.bar(top_uf, x="Campi", y="UF", orientation="h", color="Campi",
    color_continuous_scale="Greens", text="Campi", title="Estados com Mais Campi da Rede Federal")
fig_uf.update_layout(height=400, yaxis=dict(categoryorder="total ascending"), showlegend=False, margin=dict(l=0, r=0, t=50, b=0))
fig_uf.update_traces(textposition="outside")
st.plotly_chart(fig_uf, use_container_width=True)

# Top instituições por número de campi
top_inst_campi = df_reg.groupby("instituicao").size().sort_values(ascending=False).head(15).reset_index(name="Campi")
fig_top = px.bar(top_inst_campi, x="Campi", y="instituicao", orientation="h", color="Campi",
    color_continuous_scale="Greens", text="Campi", title="Instituições com Mais Campi")
fig_top.update_layout(height=450, yaxis=dict(categoryorder="total ascending"), showlegend=False, margin=dict(l=0, r=0, t=50, b=0))
fig_top.update_traces(textposition="outside")
st.plotly_chart(fig_top, use_container_width=True)

st.markdown("---")
st.markdown(f"""
<div style="text-align:center; color:#666; font-size:0.85rem; padding:1rem;">
    Cadastro da Rede Federal de Educação — Dados ENEM/INEP (2014–2025) | {datetime.now().strftime('%B %Y')}<br>
    {len(df_reg):,} campi de {df_reg['instituicao'].nunique()} instituições em {df_reg['uf'].nunique()} estados.<br>
    Desenvolvido por luciano.espiriao@ifmg.edu.br. 2026 - Todos os direitos reservados.
</div>
""", unsafe_allow_html=True)
