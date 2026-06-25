import streamlit as st

st.set_page_config(page_title="ENEM 2014-2025", layout="wide", page_icon="")


def pagina_home():
    import pandas as pd
    from dados_compartilhados import carregar_dados, carregar_campi_if, preparar_dados_if, carregar_rede_federal, preparar_dados_rede_federal
    from datetime import datetime

    st.markdown("""
    <style>
        .title { font-size: 3rem; font-weight: 800; letter-spacing: -1px; margin-bottom: 0; }
        .subtitle { font-size: 1.1rem; color: #888; margin-top: 0; }
        .kpi-card { background: #0e1117; border: 1px solid #333; border-radius: 12px; padding: 1.2rem 1.5rem; text-align: center; }
        .kpi-value { font-size: 2.2rem; font-weight: 700; }
        .kpi-label { font-size: 0.8rem; color: #888; text-transform: uppercase; letter-spacing: 1px; }
        .card { background: linear-gradient(135deg, #1a1a2e, #16213e); border-radius: 12px; padding: 1.5rem; margin: 0.5rem 0; border: 1px solid #333; }
        .card h3 { margin: 0 0 0.5rem 0; color: #4ecdc4; }
        .card p { margin: 0; color: #ccc; font-size: 0.95rem; }
        h2 { margin-top: 0.5rem; }
    </style>
    """, unsafe_allow_html=True)

    with st.spinner("Carregando dados..."):
        df = carregar_dados()
        campi = carregar_campi_if()
        df_if = preparar_dados_if(df, campi)
        campi_rede = carregar_rede_federal()
        df_rede = preparar_dados_rede_federal(df, campi_rede)

    st.markdown('<p class="title">   ENEM 2014–2025</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">   Uma década de educação brasileira em dados — tendências, desigualdades e surpresas</p>', unsafe_allow_html=True)

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""<div class="kpi-card"><div class="kpi-value" style="color:#4ecdc4">{len(df):,}</div><div class="kpi-label">Registros Analisados</div></div>""", unsafe_allow_html=True)
    with k2:
        st.markdown(f"""<div class="kpi-card"><div class="kpi-value" style="color:#3498db">{df['ANO'].nunique()}</div><div class="kpi-label">Anos (2014-2025)</div></div>""", unsafe_allow_html=True)
    with k3:
        total_inst = df_rede['INSTITUICAO'].nunique()
        st.markdown(f"""<div class="kpi-card"><div class="kpi-value" style="color:#2ecc71">{total_inst}</div><div class="kpi-label">Instituições da Rede Federal</div></div>""", unsafe_allow_html=True)
    with k4:
        total_campi = df_rede['CAMPUS'].nunique()
        st.markdown(f"""<div class="kpi-card"><div class="kpi-value" style="color:#e94560">{total_campi}</div><div class="kpi-label">Campi Rede Federal Mapeados</div></div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("## 🧭 Navegue pelos Dashboards")

    r1c1, r1c2, r1c3 = st.columns(3)
    with r1c1:
        st.markdown("""
        <div class="card">
            <h3>📊 ENEM Nacional</h3>
            <p>Evolução das médias nacionais, redes de ensino, regiões, disciplinas, ranking de estados e projeções para o futuro.</p>
        </div>
        """, unsafe_allow_html=True)
    with r1c2:
        st.markdown("""
        <div class="card">
            <h3>🏫 Rede Federal no ENEM</h3>
            <p>Desempenho de toda a Rede Federal de Educação, Ciência e Tecnologia: IFs, CEFETs, Colégio Pedro II, UTFPR e Escolas Técnicas Vinculadas.</p>
        </div>
        """, unsafe_allow_html=True)
    with r1c3:
        st.markdown("""
        <div class="card">
            <h3>  IFMG vs Demais IFs</h3>
            <p>Comparação detalhada do IFMG com todos os outros institutos federais: desempenho, evolução, disciplinas e gap por campus.</p>
        </div>
        """, unsafe_allow_html=True)

    r2c1, r2c2, r2c3 = st.columns(3)
    with r2c1:
        st.markdown("""
        <div class="card">
            <h3>🎓 IFMG no ENEM</h3>
            <p>Trajetória detalhada do IFMG no ENEM 2014–2025: ranking de campi, evolução por disciplina, comparação com redes locais e tabela completa.</p>
        </div>
        """, unsafe_allow_html=True)
    with r2c2:
        st.markdown("""
        <div class="card">
            <h3>🔍 Minha Instituição no ENEM</h3>
            <p>Escolha qualquer Instituição Federal (IF, CEFET, UTFPR, CPII, ETV) e veja análises completas de desempenho, ranking de campi e evolução.</p>
        </div>
        """, unsafe_allow_html=True)
    with r2c3:
        st.markdown("""
        <div class="card">
            <h3>\U0001F4CB Instituições da Rede Federal</h3>
            <p>Cadastro completo de todas as instituições: localização, campi, mapa interativo, estatísticas e acesso a links externos.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(f"""
    <div style="text-align:center; color:#666; font-size:0.85rem; padding:1rem;">
        Dados ENEM/INEP (2014-2025) — {datetime.now().strftime('%B %Y')}<br>
        https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem<br>
        Desenvolvido por luciano.espiriao@ifmg.edu.br. 2026 - Todos os direitos reservados.
    </div>
    """, unsafe_allow_html=True)


pg = st.navigation([
    st.Page(pagina_home, title="🌍 Visão Geral", default=True),
    st.Page("pages/01_ENEM_Nacional.py", title="📊 ENEM Nacional"),
    st.Page("pages/02_Institutos_Federais.py", title="🏫 Rede Federal no ENEM"),
    st.Page("pages/03_IFMG_vs_Demais_IFs.py", title="⚔️ IFMG vs Demais IFs"),
    st.Page("pages/04_IFMG_no_ENEM.py", title="🎓 IFMG no ENEM"),
    st.Page("pages/05_Meu_IF_no_Enem.py", title="🔍 Minha Instituição no ENEM"),
    st.Page("pages/06_Instituicoes_da_Rede_Federal.py", title="📋 Instituições da Rede Federal"),
])
pg.run()
