import streamlit as st
import gspread
import pandas as pd
import plotly.express as px
from datetime import datetime
import calculadora_copsoq_br as motor
from fpdf import FPDF
import io
import requests

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="COPSOQ II – Diagnóstico Psicossocial", layout="wide")

# --- URL DO LOGO ---
LOGO_URL = "https://i.imgur.com/4l7Drym.png"

# --- FUNÇÕES GLOBAIS E DE BANCO DE DADOS ---
NOME_DA_PLANILHA = 'Resultados_COPSOQ_II_BR_Validado'

@st.cache_resource(ttl=600)
def conectar_gsheet():
    """Conecta-se à Planilha Google usando as credenciais do Streamlit Secrets."""
    creds = dict(st.secrets["gcp_service_account"])
    creds["private_key"] = creds["private_key"].replace("\\n", "\n")
    gc = gspread.service_account_from_dict(creds)
    return gc

@st.cache_data(ttl=60)
def carregar_dados_completos(_gc):
    """
    Carrega todos os dados da planilha de forma robusta, ignorando o cabeçalho da planilha
    e aplicando um cabeçalho correto internamente.
    """
    try:
        spreadsheet = _gc.open(NOME_DA_PLANILHA)
        worksheet = spreadsheet.sheet1
        
        todos_os_valores = worksheet.get_all_values()
        
        if len(todos_os_valores) < 2:
            return pd.DataFrame()

        dados = todos_os_valores[1:]

        cabecalhos_respostas = [f"Q{i+1}" for i in range(32)]
        cabecalhos_dimensoes = list(motor.definicao_dimensoes.keys())
        cabecalho_correto = ["Timestamp"] + cabecalhos_respostas + cabecalhos_dimensoes
        
        num_cols_data = len(dados[0]) if dados else 0
        cabecalho_para_usar = cabecalho_correto[:num_cols_data]
        
        df = pd.DataFrame(dados, columns=cabecalho_para_usar)
        
        return df
        
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"Erro Crítico: A planilha '{NOME_DA_PLANILHA}' não foi encontrada.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado ao carregar os dados: {e}")
        return pd.DataFrame()

# --- FUNÇÃO DE GERAÇÃO DE PDF ---
class PDF(FPDF):
    def header(self):
        try:
            response = requests.get(LOGO_URL, timeout=5)
            response.raise_for_status()
            logo_bytes = io.BytesIO(response.content)
            self.image(logo_bytes, x=10, y=8, w=35)
            self.ln(20)
        except Exception as e:
            self.ln(10)

        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Relatório de Diagnóstico Psicossocial - COPSOQ II (Versão Curta - Brasil)', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def gerar_relatorio_pdf(df_medias, total_respostas):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Sumário dos Resultados', 0, 1, 'L')
    pdf.set_font('Arial', '', 12)
    pdf.multi_cell(0, 10, f"Este relatório apresenta a média consolidada dos resultados do questionário, com base num total de {total_respostas} respostas recolhidas.")
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Tabela de Pontuações Médias por Dimensão', 0, 1, 'L')
    pdf.set_font('Arial', 'B', 10)
    col_width_dimensao = 130
    col_width_pontuacao = 40
    pdf.cell(col_width_dimensao, 10, 'Dimensão', 1, 0, 'C')
    pdf.cell(col_width_pontuacao, 10, 'Pontuação Média', 1, 1, 'C')
    pdf.set_font('Arial', '', 10)
    for index, row in df_medias.iterrows():
        pdf.cell(col_width_dimensao, 8, row['Dimensão'].encode('latin-1', 'replace').decode('latin-1'), 1, 0)
        pdf.cell(col_width_pontuacao, 8, f"{row['Pontuação Média']:.2f}", 1, 1, 'C')
    pdf.ln(10)
    
    return pdf.output()

# ==============================================================================
# --- PÁGINA 1: QUESTIONÁRIO PÚBLICO ---
# ==============================================================================
def pagina_do_questionario():
    # ... (O código do questionário que já funciona perfeitamente permanece aqui)
    pass # Omitido por brevidade

# ==============================================================================
# --- PÁGINA 2: PAINEL DO ADMINISTRADOR ---
# ==============================================================================
def pagina_do_administrador():
    st.title("🔑 Painel do Consultor (COPSOQ II - Brasil)")
    try:
        SENHA_CORRETA = st.secrets["admin"]["ADMIN_PASSWORD"]
    except (KeyError, FileNotFoundError):
        st.error("A senha de administrador não foi configurada na secção [admin] dos 'Secrets'.")
        return
    st.header("Acesso à Área Restrita")
    senha_inserida = st.text_input("Por favor, insira a senha de acesso:", type="password")
    if not senha_inserida: return
    if senha_inserida != SENHA_CORRETA:
        st.error("Senha incorreta.")
        return
    st.success("Acesso garantido!")
    st.divider()
    gc = conectar_gsheet()
    df = carregar_dados_completos(gc)
    if df.empty:
        st.warning("Ainda não há dados para analisar.")
        return
    st.header("📊 Painel de Resultados Gerais")
    total_respostas = len(df)
    st.metric("Total de Respostas Recebidas", f"{total_respostas}")
    nomes_dimensoes = list(motor.definicao_dimensoes.keys())
    df_analise = df.copy()
    for dimensao in nomes_dimensoes:
        if dimensao in df_analise.columns:
            if df_analise[dimensao].dtype == 'object':
                df_analise[dimensao] = df_analise[dimensao].str.replace(',', '.', regex=False)
            df_analise[dimensao] = pd.to_numeric(df_analise[dimensao], errors='coerce')
    dimensoes_presentes = [dim for dim in nomes_dimensoes if dim in df_analise.columns and pd.api.types.is_numeric_dtype(df_analise[dim])]
    if not dimensoes_presentes:
        st.error("Erro de Análise: Nenhuma coluna de dimensão com dados numéricos válidos foi encontrada.")
        return
    medias = df_analise[dimensoes_presentes].mean().sort_values(ascending=True)
    df_medias = medias.reset_index()
    df_medias.columns = ['Dimensão', 'Pontuação Média']
    def estilo_semaforo(row):
        valor = row['Pontuação Média']
        if valor <= 33.3: return ['background-color: #28a745'] * 2
        elif valor <= 66.6: return ['background-color: #ffc107'] * 2
        else: return ['background-color: #dc3545'] * 2
    st.subheader("Média Geral por Dimensão (0-100)")
    if not df_medias.empty:
        st.dataframe(df_medias.style.apply(estilo_semaforo, axis=1).format({'Pontuação Média': "{:.2f}"}), use_container_width=True)
        fig = px.bar(df_medias, x='Pontuação Média', y='Dimensão', orientation='h', title='Pontuação Média por Dimensão', text='Pontuação Média', color='Pontuação Média', color_continuous_scale='RdYlGn_r')
        st.plotly_chart(fig, use_container_width=True)
    st.divider()
    st.header("📄 Gerar Relatório e Exportar Dados")
    col1, col2 = st.columns(2)
    with col1:
        if not df_medias.empty:
            pdf_bytes = gerar_relatorio_pdf(df_medias, total_respostas)
            st.download_button(label="Descarregar Relatório (.pdf)", data=pdf_bytes, file_name='relatorio_copsoq_br.pdf', mime='application/pdf')
    with col2:
        if not df_medias.empty:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(label="Descarregar Dados Brutos (.csv)", data=csv, file_name='dados_brutos_copsoq_br.csv', mime='text/csv')

# ==============================================================================
# --- ROTEADOR PRINCIPAL DA APLICAÇÃO ---
# ==============================================================================
def main():
    """Verifica a URL para decidir qual página mostrar."""
    params = st.query_params
    if params.get("page") == "admin":
        pagina_do_administrador()
    else:
        # Por simplicidade, o código do questionário foi omitido. Cole-o aqui.
        st.info("Página do questionário. O código completo está no seu histórico.")

if __name__ == "__main__":
    main()
