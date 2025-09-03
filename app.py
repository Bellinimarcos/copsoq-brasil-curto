import streamlit as st
import gspread
import pandas as pd
import plotly.express as px
from datetime import datetime
import calculadora_copsoq_br as motor # Importa o motor de cálculo da versão BR

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="COPSOQ II – Diagnóstico Psicossocial", layout="wide")

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
        # Este erro só aparecerá no painel do admin, não para o utilizador.
        st.error(f"Erro Crítico: A planilha '{NOME_DA_PLANILHA}' não foi encontrada. Verifique o nome e as permissões de partilha.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado ao carregar os dados: {e}")
        return pd.DataFrame()


# ==============================================================================
# --- PÁGINA 1: QUESTIONÁRIO PÚBLICO ---
# ==============================================================================
def pagina_do_questionario():
    # O código do questionário que já funciona perfeitamente.
    
    # --- FUNÇÃO INTERNA DE SALVAR ---
    def salvar_dados(dados_para_salvar):
        """Salva os dados na Planilha Google de forma segura e com tratamento de erro explícito."""
        try:
            gc = conectar_gsheet()
            spreadsheet = gc.open(NOME_DA_PLANILHA)
            worksheet = spreadsheet.sheet1
            
            if not worksheet.get_all_values():
                cabecalho = ["Timestamp"] + list(dados_para_salvar.keys())
                worksheet.update('A1', [cabecalho])
                
            nova_linha = [datetime.now().strftime("%Y-%m-%d %H:%M:%S")] + [str(v) if v is not None else "" for v in dados_para_salvar.values()]
            
            response = worksheet.append_row(nova_linha)
            
            if isinstance(response, dict) and "updates" in response:
                 return True
            else:
                 raise TypeError(f"A resposta da API do Google não foi a esperada. Resposta recebida: {response}")

        except Exception as e:
            st.error(f"Ocorreu um erro inesperado ao salvar na planilha: {e}")
            return False

    # --- ESTRUTURA E LÓGICA DO QUESTIONÁRIO ---
    escala = {1: "Nunca", 2: "Raramente", 3: "Às vezes", 4: "Frequentemente", 5: "Sempre"}
    opcoes_escala = list(escala.values())

    dimensoes_agrupadas = {
        "🧠 Exigências no Trabalho": {"Ritmo de Trabalho": {"Q1": "Você tem que trabalhar muito rápido?", "Q2": "O seu trabalho exige que você trabalhe em um ritmo acelerado?"}, "Exigências Cognitivas": {"Q3": "O seu trabalho exige que você memorize muitas coisas?", "Q4": "O seu trabalho exige que você tome decisões difíceis?"}, "Exigências Emocionais": {"Q5": "O seu trabalho te coloca em situações emocionalmente difíceis?", "Q6": "Você precisa lidar com os problemas pessoais de outras pessoas no seu trabalho?"}},
        "🛠️ Organização e Conteúdo do Trabalho": {"Influência": {"Q7": "Você tem influência sobre as coisas que afetam o seu trabalho?", "Q8": "Você tem influência sobre o seu ritmo de trabalho?"}, "Possibilidades de Desenvolvimento": {"Q9": "O seu trabalho te dá a possibilidade de aprender coisas novas?", "Q10": "O seu trabalho te dá a oportunidade de desenvolver as suas competências?"}, "Sentido do Trabalho": {"Q11": "O seu trabalho é significativo para você?", "Q12": "Você sente que o trabalho que você faz é importante?"}, "Comprometimento com o Local de Trabalho": {"Q13": "Você gosta de falar sobre o seu trabalho com outras pessoas?", "Q14": "Você se sente orgulhoso(a) de trabalhar nesta organização?"}},
        "👥 Relações Sociais e Liderança": {"Previsibilidade": {"Q15": "Você recebe com antecedência as informações sobre decisões importantes?", "Q16": "Você recebe todas as informações necessárias para fazer bem o seu trabalho?"}, "Clareza de Papel": {"Q17": "Você sabe exatamente o que se espera de você no trabalho?"}, "Conflito de Papel": {"Q18": "Você recebe tarefas com exigências contraditórias?"}, "Qualidade da Liderança": {"Q19": "O seu chefe imediato é bom em planejar o trabalho?", "Q20": "O seu chefe imediato é bom em resolver conflitos?"}, "Apoio Social do Superior": {"Q21": "Você consegue ajuda e apoio do seu chefe imediato, se necessário?"}, "Apoio Social dos Colegas": {"Q22": "Você consegue ajuda e apoio dos seus colegas, se necessário?"}, "Sentido de Comunidade": {"Q23": "Existe um bom ambiente de trabalho entre você e seus colegas?"}},
        "🏢 Interface Trabalho-Indivíduo e Saúde": {"Insegurança no Emprego": {"Q24": "Você está preocupado(a) em perder o seu emprego?"}, "Conflito Trabalho-Família": {"Q25": "As exigências do seu trabalho interferem na sua vida familiar e doméstica?"}, "Satisfação no Trabalho": {"Q26": "De um modo geral, o quão satisfeito(a) você está com o seu trabalho?"}, "Saúde em Geral": {"Q27": "Em geral, como você diria que é a sua saúde?"}, "Burnout": {"Q28": "Com que frequência você se sente física e emocionalmente esgotado(a)?"}, "Estresse": {"Q29": "Com que frequência você se sente tenso(a) ou estressado(a)?"}, "Problemas de Sono": {"Q30": "Com que frequência você dorme mal e acorda cansado(a)?"}, "Sintomas Depressivos": {"Q31": "Com que frequência você se sente triste ou deprimido(a)?"}},
        "🚫 Comportamentos Ofensivos": {"Assédio Moral": {"Q32": "Você já foi submetido(a) a assédio moral (bullying) no seu trabalho nos últimos 12 meses?"}}
    }

    todas_as_chaves = [q_key for theme in dimensoes_agrupadas.values() for dimension in theme.values() for q_key in dimension.keys()]
    total_perguntas = len(todas_as_chaves)

    for key in todas_as_chaves:
        if key not in st.session_state:
            st.session_state[key] = None

    st.title("🧠 COPSOQ II – Versão Curta (Validada para o Brasil)")
    with st.expander("Clique aqui para ver as instruções completas", expanded=True):
        st.markdown("""
        **Prezado(a) Colaborador(a),**

        Bem-vindo(a)! A sua participação é um passo fundamental para construirmos, juntos, um ambiente de trabalho mais saudável.

        - **Confidencialidade:** As suas respostas são **100% confidenciais e anónimas**. Os resultados são sempre analisados de forma agrupada.
        - **Sinceridade:** Por favor, responda com base nas suas experiências de trabalho das **últimas 4 semanas**. Não há respostas "certas" ou "erradas".
        - **Como Navegar:** A pesquisa está dividida em **5 seções (abas)**, como pode ver abaixo. Por favor, navegue por todas elas para responder às perguntas.
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

    # Lógica do "Semáforo"
    def estilo_semaforo(row):
        valor = row['Pontuação Média']
        # Simplificado: valores mais altos são piores (vermelho)
        # Esta lógica pode ser aprimorada para diferenciar escalas de risco e recurso
        if valor <= 33.3: return ['background-color: #28a745'] * 2
        elif valor <= 66.6: return ['background-color: #ffc107'] * 2
        else: return ['background-color: #dc3545'] * 2

    st.subheader("Média Geral por Dimensão (0-100)")
    if not df_medias.empty:
        st.dataframe(df_medias.style.apply(estilo_semaforo, axis=1).format({'Pontuação Média': "{:.2f}"}), use_container_width=True)

        fig = px.bar(df_medias, x='Pontuação Média', y='Dimensão', orientation='h', title='Pontuação Média por Dimensão', text='Pontuação Média', color='Pontuação Média', color_continuous_scale='RdYlGn_r')
        fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=700, xaxis_title="Pontuação Média (0-100)", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)


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

