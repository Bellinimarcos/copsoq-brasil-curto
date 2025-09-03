import streamlit as st
import gspread
from datetime import datetime
import calculadora_copsoq_br as motor # Importa o novo motor de cálculo validado

# --- CONFIGURAÇÃO INICIAL E ESTADO DA SESSÃO ---
st.set_page_config(page_title="COPSOQ II – Diagnóstico Psicossocial", layout="wide")

# Inicializa o session_state para armazenar as respostas de forma segura
if 'respostas_br_validado' not in st.session_state:
    st.session_state.respostas_br_validado = {}

# --- FUNÇÕES DE APOIO (CONEXÃO COM GOOGLE SHEETS) ---
NOME_DA_PLANILHA = 'Resultados_COPSOQ_II_BR_Validado'

def salvar_dados(dados_para_salvar):
    """Salva os dados na Planilha Google de forma segura."""
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
        worksheet.append_row(nova_linha)
        return True
    except Exception as e:
        st.error(f"Ocorreu um erro ao salvar na planilha: {e}")
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

total_perguntas = sum(len(perguntas) for dim in dimensoes_agrupadas.values() for perguntas in dim.values())

# --- INTERFACE PRINCIPAL ---
st.title("🧠 COPSOQ II – Versão Curta (Validada para o Brasil)")
with st.expander("Clique aqui para ver as instruções completas", expanded=True):
    st.markdown("""
    **Prezado(a) Colaborador(a),**
    Bem-vindo(a)! Sua participação é confidencial e anônima. Por favor, responda com base nas suas experiências de trabalho para nos ajudar a construir um ambiente melhor.
    """)
st.divider()

# --- BARRA DE PROGRESSO ---
perguntas_respondidas = len(st.session_state.respostas_br_validado)
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
                resposta_guardada = st.session_state.respostas_br_validado.get(q_key)
                indice = opcoes_escala.index(resposta_guardada) if resposta_guardada in opcoes_escala else None
                resposta = st.radio(label=q_text, options=opcoes_escala, key=q_key, horizontal=True, index=indice)
                if resposta:
                    st.session_state.respostas_br_validado[q_key] = resposta
            st.markdown("---")

# --- LÓGICA DE FINALIZAÇÃO E ENVIO ---
if progresso == 1.0:
    st.success("🎉 **Excelente! Você respondeu a todas as perguntas.**")
    if st.button("Enviar Respostas", type="primary", use_container_width=True):
        with st.spinner('Calculando e enviando...'):
            resultados_dimensoes = motor.calcular_dimensoes(st.session_state.respostas_br_validado)
            dados_completos = {**st.session_state.respostas_br_validado, **resultados_dimensoes}
            if salvar_dados(dados_completos):
                st.session_state.respostas_br_validado.clear()
                st.balloons()
                st.success("✅ Respostas enviadas com sucesso. Muito obrigado!")
                st.rerun()
else:
    st.warning("Por favor, navegue por todas as abas e responda às perguntas restantes.")

