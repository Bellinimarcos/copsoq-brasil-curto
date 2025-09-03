import streamlit as st

# --- CONFIGURAÇÃO INICIAL E ESTADO DA SESSÃO ---
st.set_page_config(page_title="COPSOQ III – Diagnóstico Psicossocial", layout="wide")

# Inicializa o session_state para armazenar as respostas de forma segura
if 'respostas_br' not in st.session_state:
    st.session_state.respostas_br = {}

# --- ESTRUTURA DE DADOS DO QUESTIONÁRIO ---
# Escala de resposta padrão
escala = {1: "Nunca", 2: "Raramente", 3: "Às vezes", 4: "Frequentemente", 5: "Sempre"}
opcoes_escala = list(escala.values())

# Dicionário com todas as dimensões e perguntas, agrupadas por temas
dimensoes_agrupadas = {
    "🧠 Exigências no Trabalho": {
        "1. Exigências Cognitivas": ["O seu trabalho exige que você pense rápido?", "Você precisa lembrar de muitas coisas no trabalho?", "O seu trabalho exige que você tome decisões difíceis?"],
        "2. Exigências Emocionais": ["O seu trabalho exige que você esconda suas emoções?", "Você precisa lidar com pessoas difíceis no trabalho?"],
        "3. Ritmo de Trabalho": ["Você tem que trabalhar muito intensamente?", "O seu trabalho exige que você seja rápido?"]
    },
    "🛠️ Organização do Trabalho e Autonomia": {
        "4. Influência no Trabalho": ["Você tem influência sobre como realiza seu trabalho?", "Você pode decidir quando fazer suas tarefas?"],
        "5. Possibilidades de Desenvolvimento": ["O seu trabalho oferece oportunidades para aprender coisas novas?", "Você sente que pode se desenvolver profissionalmente?"],
        "6. Sentido do Trabalho": ["Você sente que o seu trabalho é significativo?", "Você sente orgulho do seu trabalho?"],
        "7. Previsibilidade": ["Você sabe com antecedência o que vai fazer no trabalho?", "Você recebe informações suficientes sobre mudanças no trabalho?"],
        "8. Clareza de Papéis": ["Você sabe exatamente quais são suas responsabilidades?", "Você entende o que se espera de você no trabalho?"]
    },
    "👥 Relações e Liderança": {
        "9. Reconhecimento": ["Seu trabalho é reconhecido pelos seus superiores?", "Você recebe elogios pelo seu desempenho?"],
        "10. Apoio Social dos Colegas": ["Você recebe ajuda dos seus colegas quando precisa?", "Você sente que pode contar com seus colegas?"],
        "11. Apoio Social da Liderança": ["Seu supervisor se preocupa com você?", "Você recebe apoio da liderança quando enfrenta dificuldades?"],
        "12. Qualidade da Liderança": ["Seu supervisor é bom em resolver conflitos?", "Seu supervisor comunica claramente as metas?"],
        "13. Justiça Organizacional": ["As decisões no trabalho são tomadas de forma justa?", "Você sente que é tratado com respeito?"],
        "14. Confiança Vertical": ["Você confia na liderança da sua organização?", "A liderança age com transparência?"]
    },
    "🏢 Ambiente e Segurança": {
        "15. Comunidade no Local de Trabalho": ["Você sente que pertence ao seu grupo de trabalho?", "Há um bom espírito de equipe?"],
        "16. Segurança no Trabalho": ["Você sente que seu emprego está seguro?", "Você teme ser demitido?"],
        "17. Comportamentos Ofensivos": ["Você já foi alvo de bullying no trabalho?", "Já presenciou comportamentos agressivos entre colegas?"]
    },
    "❤️ Saúde e Bem-Estar": {
        "18. Estresse": ["Você se sente estressado com o trabalho?", "O trabalho afeta negativamente sua saúde mental?"],
        "19. Sintomas Físicos": ["Você tem dores físicas relacionadas ao trabalho?", "O trabalho causa cansaço físico excessivo?"],
        "20. Problemas de Sono": ["Você tem dificuldade para dormir por causa do trabalho?", "Você acorda pensando em problemas do trabalho?"],
        "21. Satisfação no Trabalho": ["Você está satisfeito com seu trabalho atual?", "Você recomendaria seu trabalho para outras pessoas?"],
        "22. Engajamento no Trabalho": ["Você se sente envolvido com as atividades do seu trabalho?", "Você se sente motivado para ir trabalhar?"]
    }
}

# Calcula o total de perguntas para a barra de progresso
total_perguntas = sum(len(perguntas) for dim in dimensoes_agrupadas.values() for perguntas in dim.values())

# --- INTERFACE PRINCIPAL ---
st.title("🧠 COPSOQ III – Versão Curta (Brasil)")
with st.expander("Clique aqui para ver as instruções completas", expanded=True):
    st.markdown("""
    **Prezado(a) Colaborador(a),**

    Bem-vindo(a)! Sua participação é um passo fundamental para construirmos, juntos, um ambiente de trabalho mais saudável.

    - **Confidencialidade:** Suas respostas são **100% confidenciais e anônimas**. Os resultados são sempre analisados de forma agrupada.
    - **Sinceridade:** Por favor, responda com base nas suas experiências de trabalho. Não há respostas "certas" ou "erradas".
    - **Como Navegar:** A pesquisa está dividida em **5 seções (abas)**. Por favor, navegue por todas elas e responda a todas as perguntas.
    """)
st.divider()

# --- BARRA DE PROGRESSO ---
perguntas_respondidas = len(st.session_state.respostas_br)
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
            for pergunta in perguntas:
                # Armazena a resposta no session_state para persistência entre abas
                resposta = st.radio(
                    label=pergunta,
                    options=opcoes_escala,
                    key=pergunta,
                    horizontal=True,
                    index=None # Começa sem nenhuma opção selecionada
                )
                if resposta:
                    st.session_state.respostas_br[pergunta] = resposta
            st.markdown("---")


# --- LÓGICA DE FINALIZAÇÃO E ENVIO ---
if progresso == 1.0:
    st.success("🎉 **Excelente! Você respondeu a todas as perguntas.**")
    st.markdown("Clique no botão abaixo para finalizar e enviar suas respostas.")
    if st.button("Enviar Respostas", type="primary", use_container_width=True):
        with st.spinner('Enviando...'):
            #
            # NESTE PONTO, ADICIONAREMOS A LÓGICA PARA SALVAR OS DADOS
            # Ex: salvar_dados_no_google_sheets(st.session_state.respostas_br)
            #
            st.session_state.respostas_br = {} # Limpa o estado para um próximo preenchimento
            st.balloons()
            st.success("✅ Respostas enviadas com sucesso. Muito obrigado pela sua participação!")
else:
    st.warning("Por favor, navegue por todas as abas e responda às perguntas restantes para habilitar o botão de envio.")
