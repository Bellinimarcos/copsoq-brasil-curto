import streamlit as st
import gspread
from datetime import datetime
import calculadora_copsoq_br as motor # Importa o motor de cálculo da versão BR

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="COPSOQ II – Diagnóstico Psicossocial", layout="wide")

# --- FUNÇÕES DE APOIO (CONEXÃO COM GOOGLE SHEETS) ---
NOME_DA_PLANILHA = 'Resultados_COPSOQ_II_BR_Validado'

def salvar_dados(dados_para_salvar):
    """Salva os dados na Planilha Google de forma segura e com tratamento de erro explícito."""
    try:
        creds = dict(st.secrets["gcp_service_account"])
        creds["private_key"] = creds["private_key"].replace("\\n", "\n")
        gc = gspread.service_account_from_dict(creds)
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

    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"Erro Crítico: A planilha '{NOME_DA_PLANILHA}' não foi encontrada. Verifique o nome e as permissões de partilha.")
        return False
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado ao salvar na planilha: {e}")
        st.error(f"Tipo do Erro: {type(e)}")
        return False

# --- ESTRUTURA DE DADOS DO QUESTIONÁRIO (VALIDADA) ---
escala = {1: "Nunca", 2: "Raramente", 3: "Às vezes", 4: "Frequentemente", 5: "Sempre"}
opcoes_escala = list(escala.values())

dimensoes_agrupadas = {
    "🧠 Exigências no Trabalho": {
        "Ritmo de Trabalho": {"Q1": "Você tem que trabalhar muito rápido?", "Q2": "O seu trabalho exige que você trabalhe em um ritmo acelerado?"},
        "Exigências Cognitivas": {"Q3": "O seu trabalho exige que você memorize muitas coisas?", "Q4": "O seu trabalho exige que você tome decisões difíceis?"},
        "Exigências Emocionais": {"Q5": "O seu trabalho te coloca em situações emocionalmente difíceis?", "Q6": "Você precisa lidar com os problemas pessoais de outras pessoas no seu trabalho?"}
    },
    "🛠️ Organização e Conteúdo do Trabalho": {
        "Influência": {"Q7": "Você tem influência sobre as coisas que afetam o seu trabalho?", "Q8": "Você tem influência sobre o seu ritmo de trabalho?"},
        "Possibilidades de Desenvolvimento": {"Q9": "O seu trabalho te dá a possibilidade de aprender coisas novas?", "Q10": "O seu trabalho te dá a oportunidade de desenvolver as suas competências?"},
        "Sentido do Trabalho": {"Q11": "O seu trabalho é significativo para você?", "Q12": "Você sente que o trabalho que você faz é importante?"},
        "Comprometimento com o Local de Trabalho": {"Q13": "Você gosta de falar sobre o seu trabalho com outras pessoas?", "Q14": "Você se sente orgulhoso(a) de trabalhar nesta organização?"}
    },
    "👥 Relações Sociais e Liderança": {
        "Previsibilidade": {"Q15": "Você recebe com antecedência as informações sobre decisões importantes?", "Q16": "Você recebe todas as informações necessárias para fazer bem o seu trabalho?"},
        "Clareza de Papel": {"Q17": "Você sabe exatamente o que se espera de você no trabalho?"},
        "Conflito de Papel": {"Q18": "Você recebe tarefas com exigências contraditórias?"},
        "Qualidade da Liderança": {"Q19": "O seu chefe imediato é bom em planejar o trabalho?", "Q20": "O seu chefe imediato é bom em resolver conflitos?"},
        "Apoio Social do Superior": {"Q21": "Você consegue ajuda e apoio do seu chefe imediato, se necessário?"},
        "Apoio Social dos Colegas": {"Q22": "Você consegue ajuda e apoio dos seus colegas, se necessário?"},
        "Sentido de Comunidade": {"Q23": "Existe um bom ambiente de trabalho entre você e seus colegas?"}
    },
    "🏢 Interface Trabalho-Indivíduo e Saúde": {
        "Insegurança no Emprego": {"Q24": "Você está preocupado(a) em perder o seu emprego?"},
        "Conflito Trabalho-Família": {"Q25": "As exigências do seu trabalho interferem na sua vida familiar e doméstica?"},
        "Satisfação no Trabalho": {"Q26": "De um modo geral, o quão satisfeito(a) você está com o seu trabalho?"},
        "Saúde em Geral": {"Q27": "Em geral, como você diria que é a sua saúde?"},
        "Burnout": {"Q28": "Com que frequência você se sente física e emocionalmente esgotado(a)?"},
        "Estresse": {"Q29": "Com que frequência você se sente tenso(a) ou estressado(a)?"},
        "Problemas de Sono": {"Q30": "Com que frequência você dorme mal e acorda cansado(a)?"},
        "Sintomas Depressivos": {"Q31": "Com que frequência você se sente triste ou deprimido(a)?"}
    },
    "🚫 Comportamentos Ofensivos": {
        "Assédio Moral": {"Q32": "Você já foi submetido(a) a assédio moral (bullying) no seu trabalho nos últimos 12 meses?"}
    }
}

# Cria uma lista única com todas as chaves das perguntas (ex: Q1, Q2...)
todas_as_chaves = [q_key for theme in dimensoes_agrupadas.values() for dimension in theme.values() for q_key in dimension.keys()]
total_perguntas = len(todas_as_chaves)

# --- INICIALIZAÇÃO DO ESTADO DA SESSÃO ---
# Garante que cada chave de pergunta exista no estado da sessão
for key in todas_as_chaves:
    if key not in st.session_state:
        st.session_state[key] = None

# --- INTERFACE PRINCIPAL ---
st.title("🧠 COPSOQ II – Versão Curta (Validada para o Brasil)")

# --- INSTRUÇÕES APRIMORADAS ---
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

# --- BARRA DE PROGRESSO ---
perguntas_respondidas = len([key for key in todas_as_chaves if st.session_state[key] is not None])
progresso = perguntas_respondidas / total_perguntas if total_perguntas > 0 else 0
st.progress(progresso, text=f"Progresso: {perguntas_respondidas} de {total_perguntas} perguntas respondidas ({progresso:.0%})")
st.markdown("---")

# --- NAVEGAÇÃO POR ABAS ---
lista_de_abas = list(dimensoes_agrupadas.keys())
tabs = st.tabs(lista_de_abas)

for i, (nome_tema, dimensoes) in enumerate(dimensoes_agrupadas.items()):
    with tabs[i]:
        for titulo_dimensao, perguntas in dimensoes.items():
            st.subheader(titulo_dimensao)
            for q_key, q_text in perguntas.items():
                # O widget radio agora lê e escreve diretamente em st.session_state[q_key]
                st.radio(label=q_text, options=opcoes_escala, key=q_key, horizontal=True)
            st.markdown("---")

# --- LÓGICA DE FINALIZAÇÃO E ENVIO ---
# A verificação do progresso é feita aqui, no final do script, após todos os widgets terem sido processados.
if progresso == 1.0:
    st.success("🎉 **Excelente! Você respondeu a todas as perguntas.**")
    if st.button("Enviar Respostas", type="primary", use_container_width=True):
        with st.spinner('Calculando e enviando...'):
            # Cria o dicionário de respostas a partir do estado da sessão
            respostas_para_salvar = {key: st.session_state[key] for key in todas_as_chaves}
            
            resultados_dimensoes = motor.calcular_dimensoes(respostas_para_salvar)
            dados_completos = {**respostas_para_salvar, **resultados_dimensoes}
            
            if salvar_dados(dados_completos):
                # Limpa o estado da sessão para o próximo utilizador
                for key in todas_as_chaves:
                    del st.session_state[key]
                st.balloons()
                st.success("✅ Respostas enviadas com sucesso. Muito obrigado!")
                st.rerun()
else:
    st.warning("Por favor, navegue por todas as abas e responda às perguntas restantes.")

import streamlit as st
import gspread
from datetime import datetime
import calculadora_copsoq_br as motor # Importa o motor de cálculo da versão BR

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="COPSOQ II – Diagnóstico Psicossocial", layout="wide")

# --- FUNÇÕES DE APOIO (CONEXÃO COM GOOGLE SHEETS) ---
NOME_DA_PLANILHA = 'Resultados_COPSOQ_II_BR_Validado'

def salvar_dados(dados_para_salvar):
    """Salva os dados na Planilha Google de forma segura e com tratamento de erro explícito."""
    try:
        creds = dict(st.secrets["gcp_service_account"])
        creds["private_key"] = creds["private_key"].replace("\\n", "\n")
        gc = gspread.service_account_from_dict(creds)
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

    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"Erro Crítico: A planilha '{NOME_DA_PLANILHA}' não foi encontrada. Verifique o nome e as permissões de partilha.")
        return False
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado ao salvar na planilha: {e}")
        st.error(f"Tipo do Erro: {type(e)}")
        return False

# --- ESTRUTURA DE DADOS DO QUESTIONÁRIO (VALIDADA) ---
escala = {1: "Nunca", 2: "Raramente", 3: "Às vezes", 4: "Frequentemente", 5: "Sempre"}
opcoes_escala = list(escala.values())

dimensoes_agrupadas = {
    "🧠 Exigências no Trabalho": {
        "Ritmo de Trabalho": {"Q1": "Você tem que trabalhar muito rápido?", "Q2": "O seu trabalho exige que você trabalhe em um ritmo acelerado?"},
        "Exigências Cognitivas": {"Q3": "O seu trabalho exige que você memorize muitas coisas?", "Q4": "O seu trabalho exige que você tome decisões difíceis?"},
        "Exigências Emocionais": {"Q5": "O seu trabalho te coloca em situações emocionalmente difíceis?", "Q6": "Você precisa lidar com os problemas pessoais de outras pessoas no seu trabalho?"}
    },
    "🛠️ Organização e Conteúdo do Trabalho": {
        "Influência": {"Q7": "Você tem influência sobre as coisas que afetam o seu trabalho?", "Q8": "Você tem influência sobre o seu ritmo de trabalho?"},
        "Possibilidades de Desenvolvimento": {"Q9": "O seu trabalho te dá a possibilidade de aprender coisas novas?", "Q10": "O seu trabalho te dá a oportunidade de desenvolver as suas competências?"},
        "Sentido do Trabalho": {"Q11": "O seu trabalho é significativo para você?", "Q12": "Você sente que o trabalho que você faz é importante?"},
        "Comprometimento com o Local de Trabalho": {"Q13": "Você gosta de falar sobre o seu trabalho com outras pessoas?", "Q14": "Você se sente orgulhoso(a) de trabalhar nesta organização?"}
    },
    "👥 Relações Sociais e Liderança": {
        "Previsibilidade": {"Q15": "Você recebe com antecedência as informações sobre decisões importantes?", "Q16": "Você recebe todas as informações necessárias para fazer bem o seu trabalho?"},
        "Clareza de Papel": {"Q17": "Você sabe exatamente o que se espera de você no trabalho?"},
        "Conflito de Papel": {"Q18": "Você recebe tarefas com exigências contraditórias?"},
        "Qualidade da Liderança": {"Q19": "O seu chefe imediato é bom em planejar o trabalho?", "Q20": "O seu chefe imediato é bom em resolver conflitos?"},
        "Apoio Social do Superior": {"Q21": "Você consegue ajuda e apoio do seu chefe imediato, se necessário?"},
        "Apoio Social dos Colegas": {"Q22": "Você consegue ajuda e apoio dos seus colegas, se necessário?"},
        "Sentido de Comunidade": {"Q23": "Existe um bom ambiente de trabalho entre você e seus colegas?"}
    },
    "🏢 Interface Trabalho-Indivíduo e Saúde": {
        "Insegurança no Emprego": {"Q24": "Você está preocupado(a) em perder o seu emprego?"},
        "Conflito Trabalho-Família": {"Q25": "As exigências do seu trabalho interferem na sua vida familiar e doméstica?"},
        "Satisfação no Trabalho": {"Q26": "De um modo geral, o quão satisfeito(a) você está com o seu trabalho?"},
        "Saúde em Geral": {"Q27": "Em geral, como você diria que é a sua saúde?"},
        "Burnout": {"Q28": "Com que frequência você se sente física e emocionalmente esgotado(a)?"},
        "Estresse": {"Q29": "Com que frequência você se sente tenso(a) ou estressado(a)?"},
        "Problemas de Sono": {"Q30": "Com que frequência você dorme mal e acorda cansado(a)?"},
        "Sintomas Depressivos": {"Q31": "Com que frequência você se sente triste ou deprimido(a)?"}
    },
    "🚫 Comportamentos Ofensivos": {
        "Assédio Moral": {"Q32": "Você já foi submetido(a) a assédio moral (bullying) no seu trabalho nos últimos 12 meses?"}
    }
}

# Cria uma lista única com todas as chaves das perguntas (ex: Q1, Q2...)
todas_as_chaves = [q_key for theme in dimensoes_agrupadas.values() for dimension in theme.values() for q_key in dimension.keys()]
total_perguntas = len(todas_as_chaves)

# --- INICIALIZAÇÃO DO ESTADO DA SESSÃO ---
# Garante que cada chave de pergunta exista no estado da sessão
for key in todas_as_chaves:
    if key not in st.session_state:
        st.session_state[key] = None

# --- INTERFACE PRINCIPAL ---
st.title("🧠 COPSOQ II – Versão Curta (Validada para o Brasil)")

# --- INSTRUÇÕES APRIMORADAS ---
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

# --- BARRA DE PROGRESSO ---
perguntas_respondidas = len([key for key in todas_as_chaves if st.session_state[key] is not None])
progresso = perguntas_respondidas / total_perguntas if total_perguntas > 0 else 0
st.progress(progresso, text=f"Progresso: {perguntas_respondidas} de {total_perguntas} perguntas respondidas ({progresso:.0%})")
st.markdown("---")

# --- NAVEGAÇÃO POR ABAS ---
lista_de_abas = list(dimensoes_agrupadas.keys())
tabs = st.tabs(lista_de_abas)

for i, (nome_tema, dimensoes) in enumerate(dimensoes_agrupadas.items()):
    with tabs[i]:
        for titulo_dimensao, perguntas in dimensoes.items():
            st.subheader(titulo_dimensao)
            for q_key, q_text in perguntas.items():
                # O widget radio agora lê e escreve diretamente em st.session_state[q_key]
                st.radio(label=q_text, options=opcoes_escala, key=q_key, horizontal=True)
            st.markdown("---")

# --- LÓGICA DE FINALIZAÇÃO E ENVIO ---
# A verificação do progresso é feita aqui, no final do script, após todos os widgets terem sido processados.
if progresso == 1.0:
    st.success("🎉 **Excelente! Você respondeu a todas as perguntas.**")
    if st.button("Enviar Respostas", type="primary", use_container_width=True):
        with st.spinner('Calculando e enviando...'):
            # Cria o dicionário de respostas a partir do estado da sessão
            respostas_para_salvar = {key: st.session_state[key] for key in todas_as_chaves}
            
            resultados_dimensoes = motor.calcular_dimensoes(respostas_para_salvar)
            dados_completos = {**respostas_para_salvar, **resultados_dimensoes}
            
            if salvar_dados(dados_completos):
                # Limpa o estado da sessão para o próximo utilizador
                for key in todas_as_chaves:
                    del st.session_state[key]
                st.balloons()
                st.success("✅ Respostas enviadas com sucesso. Muito obrigado!")
                st.rerun()
else:
    st.warning("Por favor, navegue por todas as abas e responda às perguntas restantes.")

