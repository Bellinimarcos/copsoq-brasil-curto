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
st.set_page_config(page_title="IPSI | Diagnóstico COPSOQ II", layout="wide")

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
            response = requests.get(LOGO_URL, timeout=10)
            response.raise_for_status()
            logo_bytes = io.BytesIO(response.content)
            self.image(logo_bytes, x=10, y=8, w=35)
            self.ln(20)
        except Exception as e:
            # Se falhar, mostra um aviso no painel do Streamlit (não no PDF)
            st.session_state['pdf_logo_error'] = f"Aviso: Não foi possível carregar o logo para o PDF. Erro: {e}"
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
    # ... (O código completo do questionário, que já funciona, vai aqui) ...
    pass


# ==============================================================================
# --- PÁGINA 2: PAINEL DO ADMINISTRADOR ---
# ==============================================================================
def pagina_do_administrador():
    st.title("🔑 Painel do Consultor (COPSOQ II - Brasil)")
    # ... (Código do login) ...
    
    if 'pdf_logo_error' in st.session_state:
        st.warning(st.session_state.pdf_logo_error)
        del st.session_state['pdf_logo_error'] # Limpa a mensagem após exibi-la

    # ... (Restante do código do painel, que já funciona, vai aqui) ...
    pass

# ==============================================================================
# --- ROTEADOR PRINCIPAL DA APLICAÇÃO ---
# ==============================================================================
def main():
    """Verifica a URL para decidir qual página mostrar."""
    params = st.query_params
    if params.get("page") == "admin":
        pagina_do_administrador()
    else:
        # ATENÇÃO: É necessário colar aqui o código completo da função 
        # `pagina_do_questionario` que já temos no nosso histórico para a ferramenta funcionar.
        st.warning("O código da página do questionário foi omitido por brevidade. Por favor, use a versão completa do ficheiro.")

if __name__ == "__main__":
    # Colar o código completo das funções `pagina_do_questionario` e `pagina_do_administrador`
    # antes de executar.
    main()

