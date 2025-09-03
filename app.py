import streamlit as st
import gspread
import pandas as pd
import plotly.express as px
from datetime import datetime
import calculadora_copsoq_br as motor # Importa o motor de cálculo da versão BR
from fpdf import FPDF
import io

# --- CONFIGURAÇÃO INICIAL E ESTADO DA SESSÃO ---
st.set_page_config(page_title="COPSOQ III - Versão Curta (Brasil)", layout="wide")

# --- FUNÇÕES GLOBAIS E DE BANCO DE DADOS ---
NOME_DA_PLANILHA = 'Resultados_COPSOQ_BR_Curto'

@st.cache_resource(ttl=600)
def conectar_gsheet():
    """Conecta-se à Planilha Google usando as credenciais do Streamlit Secrets."""
    creds = dict(st.secrets["gcp_service_account"])
    creds["private_key"] = creds["private_key"].replace("\\n", "\n")
    gc = gspread.service_account_from_dict(creds)
    return gc

@st.cache_data(ttl=60)
def carregar_dados_completos(_gc):
    """Carrega todos os dados da planilha de forma robusta."""
    try:
        spreadsheet = _gc.open(NOME_DA_PLANILHA)
        worksheet = spreadsheet.sheet1
        dados = worksheet.get_all_records()
        if not dados:
            return pd.DataFrame()
        df = pd.DataFrame(dados)
        df = df.loc[:, (df.columns != '')]
        return df
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"Erro: A planilha '{NOME_DA_PLANILHA}' não foi encontrada.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado ao carregar os dados: {e}")
        return pd.DataFrame()

# ==============================================================================
# --- PÁGINA 1: QUESTIONÁRIO PÚBLICO ---
# ==============================================================================
def pagina_do_questionario():
    if 'respostas_br' not in st.session_state:
        st.session_state.respostas_br = {}

    def salvar_dados(dados_para_salvar):
        try:
            gc = conectar_gsheet()
            spreadsheet = gc.open(NOME_DA_PLANILHA)
            worksheet = spreadsheet.sheet1
            if not worksheet.get_all_values():
                cabecalho = ["Timestamp"] + list(dados_para_salvar.keys())
                worksheet.update('A1', [cabecalho])
            nova_linha = [datetime.now().strftime("%Y-%m-%d %H:%M:%S")] + [str(v) if v is not None else "" for v in dados_para_salvar.values()]
            worksheet.append_row(nova_linha)
            return True
        except Exception as e:
            st.error(f"Ocorreu um erro ao salvar na planilha: {e}")
            return False

    escala = {1: "Nunca", 2: "Raramente", 3: "Às vezes", 4: "Frequentemente", 5: "Sempre"}
    opcoes_escala = list(escala.values())
    dimensoes_agrupadas = {
        "🧠 Exigências no Trabalho": {"1. Exigências Cognitivas": {"Q1": "O seu trabalho exige que você pense rápido?", "Q2": "Você precisa lembrar de muitas coisas no trabalho?", "Q3": "O seu trabalho exige que você tome decisões difíceis?"},"2. Exigências Emocionais": {"Q4": "O seu trabalho exige que você esconda suas emoções?", "Q5": "Você precisa lidar com pessoas difíceis no trabalho?"},"3. Ritmo de Trabalho": {"Q6": "Você tem que trabalhar muito intensamente?", "Q7": "O seu trabalho exige que você seja rápido?"}},
        "🛠️ Organização do Trabalho e Autonomia": {"4. Influência no Trabalho": {"Q8": "Você tem influência sobre como realiza seu trabalho?", "Q9": "Você pode decidir quando fazer suas tarefas?"},"5. Possibilidades de Desenvolvimento": {"Q10": "O seu trabalho oferece oportunidades para aprender coisas novas?", "Q11": "Você sente que pode se desenvolver profissionalmente?"},"6. Sentido do Trabalho": {"Q12": "Você sente que o seu trabalho é significativo?", "Q13": "Você sente orgulho do seu trabalho?"},"7. Previsibilidade": {"Q14": "Você sabe com antecedência o que vai fazer no trabalho?", "Q15": "Você recebe informações suficientes sobre mudanças no trabalho?"},"8. Clareza de Papéis": {"Q16": "Você sabe exatamente quais são suas responsabilidades?", "Q17": "Você entende o que se espera de você no trabalho?"}},
        "👥 Relações e Liderança": {"9. Reconhecimento": {"Q18": "Seu trabalho é reconhecido pelos seus superiores?", "Q19": "Você recebe elogios pelo seu desempenho?"},"10. Apoio Social dos Colegas": {"Q20": "Você recebe ajuda dos seus colegas quando precisa?", "Q21": "Você sente que pode contar com seus colegas?"},"11. Apoio Social da Liderança": {"Q22": "Seu supervisor se preocupa com você?", "Q23": "Você recebe apoio da liderança quando enfrenta dificuldades?"},"12. Qualidade da Liderança": {"Q24": "Seu supervisor é bom em resolver conflitos?", "Q25": "Seu supervisor comunica claramente as metas?"},"13. Justiça Organizacional": {"Q26": "As decisões no trabalho são tomadas de forma justa?", "Q27": "Você sente que é tratado com respeito?"},"14. Confiança Vertical": {"Q28": "Você confia na liderança da sua organização?", "Q29": "A liderança age com transparência?"}},
        "🏢 Ambiente e Segurança": {"15. Comunidade no Local de Trabalho": {"Q30": "Você sente que pertence ao seu grupo de trabalho?", "Q31": "Há um bom espírito de equipe?"},"16. Segurança no Trabalho": {"Q32": "Você sente que seu emprego está seguro?", "Q33": "Você teme ser demitido?"},"17. Comportamentos Ofensivos": {"Q34": "Você já foi alvo de bullying no trabalho?", "Q35": "Já presenciou comportamentos agressivos entre colegas?"}},
        "❤️ Saúde e Bem-Estar": {"18. Estresse": {"Q36": "Você se sente estressado com o trabalho?", "Q37": "O trabalho afeta negativamente sua saúde mental?"},"19. Sintomas Físicos": {"Q38": "Você tem dores físicas relacionadas ao trabalho?", "Q39": "O trabalho causa cansaço físico excessivo?"},"20. Problemas de Sono": {"Q40": "Você tem dificuldade para dormir por causa do trabalho?", "Q41": "Você acorda pensando em problemas do trabalho?"},"21. Satisfação no Trabalho": {"Q42": "Você está satisfeito com seu trabalho atual?", "Q43": "Você recomendaria seu trabalho para outras pessoas?"},"22. Engajamento no Trabalho": {"Q44": "Você se sente envolvido com as atividades do seu trabalho?", "Q45": "Você se sente motivado para ir trabalhar?"}}}
    total_perguntas = sum(len(perguntas) for dim in dimensoes_agrupadas.values() for perguntas in dim.values())

    st.title("🧠 COPSOQ III – Versão Curta (Brasil)")
    with st.expander("Clique aqui para ver as instruções completas", expanded=True):
        st.markdown("""
        **Prezado(a) Colaborador(a),**
        Bem-vindo(a)! Sua participação é um passo fundamental para construirmos, juntos, um ambiente de trabalho mais saudável.
        - **Confidencialidade:** Suas respostas são **100% confidenciais e anônimas**.
        - **Sinceridade:** Por favor, responda com base nas suas experiências de trabalho.
        - **Como Navegar:** A pesquisa está dividida em **5 seções (abas)**. Por favor, navegue por todas elas.
        """)
    st.divider()

    perguntas_respondidas = len(st.session_state.respostas_br)
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
                    resposta_guardada = st.session_state.respostas_br.get(q_key)
                    indice = opcoes_escala.index(resposta_guardada) if resposta_guardada in opcoes_escala else None
                    resposta = st.radio(label=q_text, options=opcoes_escala, key=q_key, horizontal=True, index=indice)
                    if resposta:
                        st.session_state.respostas_br[q_key] = resposta
                st.markdown("---")

    if progresso == 1.0:
        st.success("🎉 **Excelente! Você respondeu a todas as perguntas.**")
        if st.button("Enviar Respostas", type="primary", use_container_width=True):
            with st.spinner('Calculando e enviando...'):
                resultados_dimensoes = motor.calcular_dimensoes(st.session_state.respostas_br)
                dados_completos = {**st.session_state.respostas_br, **resultados_dimensoes}
                if salvar_dados(dados_completos):
                    st.session_state.respostas_br.clear()
                    st.balloons()
                    st.success("✅ Respostas enviadas com sucesso. Muito obrigado!")
                    st.info("Pode fechar esta janela.")
                    st.rerun()
    else:
        st.warning("Por favor, navegue por todas as abas e responda às perguntas restantes.")

# ==============================================================================
# --- PÁGINA 2: PAINEL DO ADMINISTRADOR ---
# ==============================================================================
def pagina_do_administrador():
    st.title("🔑 Painel do Consultor")
    
    try:
        SENHA_CORRETA = st.secrets["admin"]["ADMIN_PASSWORD"]
    except (KeyError, FileNotFoundError):
        st.error("A senha de administrador não foi configurada na secção [admin] dos 'Secrets'.")
        return

    st.header("Acesso à Área Restrita")
    senha_inserida = st.text_input("Por favor, insira a senha de acesso:", type="password")
    
    if not senha_inserida:
        st.info("Esta é uma área restrita para análise dos resultados consolidados.")
        return
    if senha_inserida != SENHA_CORRETA:
        st.error("Senha incorreta. Tente novamente.")
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

    # Lógica do "Semáforo" para a tabela
    def estilo_semaforo(row):
        valor = row['Pontuação Média']
        cor = 'background-color: '
        if valor <= 33.3:
            cor += '#28a745'  # Verde
        elif valor <= 66.6:
            cor += '#ffc107'  # Amarelo
        else:
            cor += '#dc3545'  # Vermelho
        return [cor, '']

    st.subheader("Média Geral por Dimensão (0-100)")
    if not df_medias.empty:
        st.dataframe(df_medias.style.apply(estilo_semaforo, axis=1).format({'Pontuação Média': "{:.2f}"}), use_container_width=True)

        fig = px.bar(df_medias, x='Pontuação Média', y='Dimensão', orientation='h', title='Pontuação Média por Dimensão', text='Pontuação Média', color='Pontuação Média', color_continuous_scale='RdYlGn_r')
        fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=700, xaxis_title="Pontuação Média (0-100)", yaxis_title="")
        fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.header("📄 Gerar Relatório e Exportar Dados")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Gerar Relatório PDF", type="primary"):
            # Para gerar o PDF, precisamos da figura `fig` definida.
            if 'fig' in locals():
                pdf_bytes = gerar_relatorio_pdf(df_medias, fig, total_respostas)
                st.download_button(label="Descarregar Relatório (.pdf)", data=pdf_bytes, file_name=f'relatorio_copsoq_br_{datetime.now().strftime("%Y%m%d")}.pdf', mime='application/pdf')
            else:
                st.warning("O gráfico precisa de ser gerado primeiro.")

    with col2:
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
        pagina_do_questionario()

if __name__ == "__main__":
    main()

