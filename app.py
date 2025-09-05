import streamlit as st
import gspread
import pandas as pd
import plotly.express as px
from datetime import datetime
import calculadora_copsoq_br as motor
from fpdf import FPDF
import io
import requests
from PIL import Image

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="IPSI | Diagnóstico COPSOQ II", layout="wide")

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
    Carrega todos os dados da planilha de forma robusta, com tratamento de erros aprimorado.
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
        st.error(f"Erro Crítico: A planilha '{NOME_DA_PLANILHA}' não foi encontrada. Verifique o nome.")
        return pd.DataFrame()
    except gspread.exceptions.APIError as e:
        st.error(
            "Erro de Permissão ao aceder ao Google Sheets. Por favor, verifique se:"
            f"\n1. A planilha '{NOME_DA_PLANILHA}' foi partilhada com o email de serviço: **{st.secrets['gcp_service_account']['client_email']}** com permissão de 'Editor'."
            "\n2. Se a permissão já foi dada, tente clicar no botão 'Limpar Cache e Recarregar Dados'."
        )
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado ao carregar os dados: {e}")
        return pd.DataFrame()

# --- LÓGICA DE GERAÇÃO DE PDF ---

def baixar_logo_em_memoria(url):
    """Baixa uma imagem de uma URL e a retorna como um objeto em memória."""
    try:
        if not url.strip(): return None, None
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, stream=True, timeout=10)
        response.raise_for_status()

        img_buffer = io.BytesIO(response.content)
        img = Image.open(img_buffer)
        
        img_format = img.format.upper()
        if img_format not in ['JPEG', 'PNG', 'GIF']:
            st.warning(f"Formato de imagem '{img_format}' não suportado. Use JPG, PNG ou GIF.")
            return None, None
        
        img_buffer.seek(0)
        return img_buffer, img_format
        
    except Exception as e:
        st.warning(f"Falha ao baixar ou processar o logo: {e}. O PDF será gerado sem ele.")
        return None, None

class PDF(FPDF):
    def __init__(self, logo_buffer=None, logo_format=None):
        super().__init__()
        self.logo_buffer = logo_buffer
        self.logo_format = logo_format

    def header_fallback_texto(self):
        """Cabeçalho de texto padrão, usado se o logo falhar."""
        self.set_font('Arial', 'B', 16)
        self.set_text_color(0, 51, 102)
        self.cell(0, 10, 'IPSI', 0, 0, 'L')
        self.ln(5)
        self.set_font('Arial', 'I', 10)
        self.set_text_color(102, 102, 102)
        self.cell(0, 10, 'Consultoria em Saúde Organizacional', 0, 1, 'L')

    def header(self):
        logo_adicionado = False
        if self.logo_buffer and self.logo_format:
            try:
                self.image(self.logo_buffer, x=10, y=8, h=12, type=self.logo_format)
                logo_adicionado = True
            except Exception:
                pass
        
        if not logo_adicionado:
            self.header_fallback_texto()
        
        self.set_line_width(0.5)
        self.set_draw_color(0, 51, 102)
        self.line(10, 25, 200, 25)
        self.ln(10)
        self.set_font('Arial', 'B', 12)
        self.set_text_color(0, 0, 0)
        self.cell(0, 10, 'Relatório de Diagnóstico Psicossocial - COPSOQ II (Versão Curta - Brasil)', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def gerar_relatorio_pdf(df_medias, total_respostas, logo_url=None):
    logo_buffer, logo_format = None, None
    if logo_url:
        logo_buffer, logo_format = baixar_logo_em_memoria(logo_url)
        
    pdf = PDF(logo_buffer=logo_buffer, logo_format=logo_format)
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
    
    buffer = io.BytesIO()
    pdf.output(buffer)
    return buffer.getvalue()

# --- PÁGINA 1: QUESTIONÁRIO PÚBLICO ---
def pagina_do_questionario():
    # O código desta função permanece inalterado
    def salvar_dados(dados_para_salvar):
        try:
            gc = conectar_gsheet()
            spreadsheet = gc.open(NOME_DA_PLANILHA)
            worksheet = spreadsheet.sheet1
            if not worksheet.get_all_values():
                cabecalho = ["Timestamp"] + list(dados_para_salvar.keys())
                worksheet.update('A1', [cabecalho])
            nova_linha = [datetime.now().strftime("%Y-%m-%d %H:%M:%S")] + [str(v) if v is not None else "" for v in dados_para_salvar.values()]
            response = worksheet.append_row(nova_linha)
            if isinstance(response, dict) and "updates" in response: return True
            else: raise TypeError(f"A resposta da API do Google não foi a esperada. Resposta recebida: {response}")
        except Exception as e:
            st.error(f"Ocorreu um erro inesperado ao salvar na planilha: {e}")
            return False

    escala = {1: "Nunca", 2: "Raramente", 3: "Às vezes", 4: "Frequentemente", 5: "Sempre"}
    opcoes_escala = list(escala.values())
    dimensoes_agrupadas = {"🧠 Exigências no Trabalho": {"Ritmo de Trabalho": {"Q1": "Você tem que trabalhar muito rápido?", "Q2": "O seu trabalho exige que você trabalhe em um ritmo acelerado?"}, "Exigências Cognitivas": {"Q3": "O seu trabalho exige que você memorize muitas coisas?", "Q4": "O seu trabalho exige que você tome decisões difíceis?"}, "Exigências Emocionais": {"Q5": "O seu trabalho te coloca em situações emocionalmente difíceis?", "Q6": "Você precisa lidar com os problemas pessoais de outras pessoas no seu trabalho?"}},"🛠️ Organização e Conteúdo do Trabalho": {"Influência": {"Q7": "Você tem influência sobre as coisas que afetam o seu trabalho?", "Q8": "Você tem influência sobre o seu ritmo de trabalho?"}, "Possibilidades de Desenvolvimento": {"Q9": "O seu trabalho te dá a possibilidade de aprender coisas novas?", "Q10": "O seu trabalho te dá a oportunidade de desenvolver as suas competências?"}, "Sentido do Trabalho": {"Q11": "O seu trabalho é significativo para você?", "Q12": "Você sente que o trabalho que você faz é importante?"}, "Comprometimento com o Local de Trabalho": {"Q13": "Você gosta de falar sobre o seu trabalho com outras pessoas?", "Q14": "Você se sente orgulhoso(a) de trabalhar nesta organização?"}},"👥 Relações Sociais e Liderança": {"Previsibilidade": {"Q15": "Você recebe com antecedência as informações sobre decisões importantes?", "Q16": "Você recebe todas as informações necessárias para fazer bem o seu trabalho?"}, "Clareza de Papel": {"Q17": "Você sabe exatamente o que se espera de você no trabalho?"}, "Conflito de Papel": {"Q18": "Você recebe tarefas com exigências contraditórias?"}, "Qualidade da Liderança": {"Q19": "O seu chefe imediato é bom em planejar o trabalho?", "Q20": "O seu chefe imediato é bom em resolver conflitos?"}, "Apoio Social do Superior": {"Q21": "Você consegue ajuda e apoio do seu chefe imediato, se necessário?"}, "Apoio Social dos Colegas": {"Q22": "Você consegue ajuda e apoio dos seus colegas, se necessário?"}, "Sentido de Comunidade": {"Q23": "Existe um bom ambiente de trabalho entre você e seus colegas?"}},"🏢 Interface Trabalho-Indivíduo e Saúde": {"Insegurança no Emprego": {"Q24": "Você está preocupado(a) em perder o seu emprego?"}, "Conflito Trabalho-Família": {"Q25": "As exigências do seu trabalho interferem na sua vida familiar e doméstica?"}, "Satisfação no Trabalho": {"Q26": "De um modo geral, o quão satisfeito(a) você está com o seu trabalho?"}, "Saúde em Geral": {"Q27": "Em geral, como você diria que é a sua saúde?"}, "Burnout": {"Q28": "Com que frequência você se sente física e emocionalmente esgotado(a)?"}, "Estresse": {"Q29": "Com que frequência você se sente tenso(a) ou estressado(a)?"}, "Problemas de Sono": {"Q30": "Com que frequência você dorme mal e acorda cansado(a)?"}, "Sintomas Depressivos": {"Q31": "Com que frequência você se sente triste ou deprimido(a)?"}},"🚫 Comportamentos Ofensivos": {"Assédio Moral": {"Q32": "Você já foi submetido(a) a assédio moral (bullying) no seu trabalho nos últimos 12 meses?"}}}
    todas_as_chaves = [q_key for theme in dimensoes_agrupadas.values() for dimension in theme.values() for q_key in dimension.keys()]
    total_perguntas = len(todas_as_chaves)

    for key in todas_as_chaves:
        if key not in st.session_state: st.session_state[key] = None

    st.title("🧠 COPSOQ II – Versão Curta (Validada para o Brasil)")
    
    with st.expander("Clique aqui para ver as instruções completas", expanded=True):
        st.markdown("""
        **Prezado(a) Colaborador(a),**

        Bem-vindo(a)! A sua participação é um passo fundamental para construirmos, juntos, um ambiente de trabalho mais saudável.

        - **Confidencialidade:** As suas respostas são **100% confidenciais e anónimas**. Os resultados são sempre analisados de forma agrupada.
        - **Sinceridade:** Por favor, responda com base nas suas experiências de trabalho das **últimas 4 semanas**. Não há respostas "certas" ou "erradas".
        - **Como Navegar:** A pesquisa está dividida em **5 seções (abas)**. Por favor, navegue por todas elas para responder às perguntas.
        - **Finalização:** O botão para enviar as suas respostas só aparecerá quando a barra de progresso atingir 100%.
        
        A sua contribuição é extremamente valiosa. Muito obrigado!
        """)
    st.divider()

    perguntas_respondidas = len([key for key in todas_as_chaves if st.session_state[key] is not None])
    progresso = perguntas_respondidas / total_perguntas if total_perguntas > 0 else 0
    st.progress(progresso, text=f"Progresso: {perguntas_respondidas} de {total_perguntas} perguntas respondidas ({progresso:.0%})")
    st.markdown("---")

    lista_de_abas = list(dimensoes_agrupadas.keys())
    tabs = st.tabs(lista_de_abas)
    for i, (nome_tema, dimensoes) in enumerate(dimensoes_agrupadas.items()):
        with tabs[i]:
            for titulo_dimensao, perguntas in dimensoes.items():
                st.subheader(titulo_dimensao)
                for q_key, q_text in perguntas.items():
                    st.radio(label=q_text, options=opcoes_escala, key=q_key, horizontal=True)
                st.markdown("---")

    if progresso == 1.0:
        st.success("🎉 **Excelente! Você respondeu a todas as perguntas.**")
        if st.button("Enviar Respostas", type="primary", use_container_width=True):
            with st.spinner('Calculando e enviando...'):
                respostas_para_salvar = {key: st.session_state[key] for key in todas_as_chaves}
                resultados_dimensoes = motor.calcular_dimensoes(respostas_para_salvar)
                dados_completos = {**respostas_para_salvar, **resultados_dimensoes}
                if salvar_dados(dados_completos):
                    for key in todas_as_chaves:
                        del st.session_state[key]
                    st.balloons()
                    st.success("✅ Respostas enviadas com sucesso. Muito obrigado!")
                    st.rerun()
    else:
        st.warning("Por favor, navegue por todas as abas e responda às perguntas restantes.")

# --- PÁGINA 2: PAINEL DO ADMINISTRADOR ---
def pagina_do_administrador():
    st.title("🔑 Painel do Consultor")
    st.markdown("Bem-vindo à área de análise de resultados do diagnóstico COPSOQ II.")

    try:
        SENHA_CORRETA = st.secrets["admin"]["ADMIN_PASSWORD"]
    except (KeyError, FileNotFoundError):
        st.error("A senha de administrador não foi configurada na secção [admin] dos 'Secrets'.")
        return

    if 'autenticado' not in st.session_state:
        st.session_state.autenticado = False

    if not st.session_state.autenticado:
        st.header("Acesso à Área Restrita")
        senha_inserida = st.text_input("Por favor, insira a senha de acesso:", type="password", key="senha")
        if st.button("Entrar"):
            if senha_inserida == SENHA_CORRETA:
                st.session_state.autenticado = True
                st.rerun()
            elif senha_inserida:
                st.error("Senha incorreta.")
        return

    st.success("Acesso garantido!")
    st.divider()
    
    # Botão para resolver problemas de conexão
    st.warning("Se encontrar um erro ou os dados parecerem desatualizados, clique no botão abaixo.")
    if st.button("🔄 Limpar Cache e Recarregar Dados"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.success("Cache limpo! A recarregar a página...")
        st.rerun()

    gc = conectar_gsheet()
    df = carregar_dados_completos(gc)

    if df.empty:
        st.info("Ainda não há dados para analisar ou ocorreu uma falha na conexão. Tente limpar o cache acima.")
        return

    total_respostas = len(df)
    st.metric("Total de Respostas Recebidas", f"{total_respostas}")
    st.divider()

    st.header("📊 Análise Geral dos Resultados")
    
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
        if valor <= 33.3: return ['background-color: #d4edda; color: #155724'] * 2
        elif valor <= 66.6: return ['background-color: #fff3cd; color: #856404'] * 2
        else: return ['background-color: #f8d7da; color: #721c24'] * 2

    tab1, tab2 = st.tabs(["Visão Gráfica", "Tabela Detalhada"])

    with tab1:
        st.subheader("Pontuação Média por Dimensão (0-100)")
        if not df_medias.empty:
            fig = px.bar(df_medias, 
                         x='Pontuação Média', 
                         y='Dimensão', 
                         orientation='h', 
                         title='Pontuação Média por Dimensão', 
                         text=df_medias['Pontuação Média'].apply(lambda x: f'{x:.2f}'),
                         color='Pontuação Média', 
                         color_continuous_scale='RdYlGn_r',
                         height=800)
            fig.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Tabela de Médias Gerais")
        if not df_medias.empty:
            st.dataframe(df_medias.style.apply(estilo_semaforo, axis=1).format({'Pontuação Média': "{:.2f}"}), use_container_width=True)

    st.divider()

    st.header("📄 Exportar Relatório e Dados")
    st.info("Para incluir um logo no relatório PDF, cole o URL da imagem no campo abaixo.")
    
    if 'logo_url' not in st.session_state:
        st.session_state.logo_url = ""

    st.text_input(
        "URL do Logo (opcional):", 
        key="logo_url", 
        placeholder="https://exemplo.com/logo.png"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if not df_medias.empty:
            pdf_bytes = gerar_relatorio_pdf(df_medias, total_respostas, st.session_state.logo_url)
            st.download_button(
                label="📥 Gerar e Descarregar Relatório (.pdf)", 
                data=pdf_bytes, 
                file_name=f'relatorio_copsoq_br_{datetime.now().strftime("%Y%m%d")}.pdf', 
                mime='application/pdf',
                use_container_width=True,
                type="primary"
            )

    with col2:
        if not df.empty:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="💾 Descarregar Dados Brutos (.csv)", 
                data=csv, 
                file_name='dados_brutos_copsoq_br.csv', 
                mime='text/csv',
                use_container_width=True
            )

# --- ROTEADOR PRINCIPAL DA APLICAÇÃO ---
def main():
    """Verifica a URL para decidir qual página mostrar."""
    params = st.query_params
    if params.get("page") == "admin":
        pagina_do_administrador()
    else:
        pagina_do_questionario()

if __name__ == "__main__":
    main()

