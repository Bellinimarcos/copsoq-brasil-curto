import streamlit as st
import gspread
from datetime import datetime
import calculadora_copsoq_br as motor # Importa o motor de cálculo da versão BR

# --- CONFIGURAÇÃO INICIAL E ESTADO DA SESSÃO ---
st.set_page_config(page_title="COPSOQ III – Diagnóstico Psicossocial", layout="wide")

# Inicializa o session_state para armazenar as respostas de forma segura
if 'respostas_br' not in st.session_state:
    st.session_state.respostas_br = {}

# --- FUNÇÕES DE APOIO (CONEXÃO COM GOOGLE SHEETS) ---
NOME_DA_PLANILHA = 'Resultados_COPSOQ_BR_Curto'

def salvar_dados(dados_para_salvar):
    """Salva os dados na Planilha Google de forma segura."""
    try:
        creds = dict(st.secrets["gcp_service_account"])
        creds["private_key"] = creds["private_key"].replace("\\n", "\n")
        gc = gspread.service_account_from_dict(creds)
        spreadsheet = gc.open(NOME_DA_PLANILHA)
        worksheet = spreadsheet.sheet1
        
        # Cria o cabeçalho se a planilha estiver vazia
        if not worksheet.get_all_values():
            cabecalho = ["Timestamp"] + list(dados_para_salvar.keys())
            worksheet.update('A1', [cabecalho])
            
        # Adiciona a nova linha de dados
        nova_linha = [datetime.now().strftime("%Y-%m-%d %H:%M:%S")] + list(dados_para_salvar.values())
        worksheet.append_row(nova_linha)
        return True
    except Exception as e:
        st.error(f"Ocorreu um erro ao salvar na planilha: {e}")
        st.error(f"Tipo do Erro: {type(e)}")
        st.info("Por favor, verifique se a planilha foi partilhada corretamente com o email de serviço e se o nome está correto.")
        return False

# --- ESTRUTURA DE DADOS DO QUESTIONÁRIO ---
escala = {1: "Nunca", 2: "Raramente", 3: "Às vezes", 4: "Frequentemente", 5: "Sempre"}
opcoes_escala = list(escala.values())

dimensoes_agrupadas = {
    "🧠 Exigências no Trabalho": {
        "1. Exigências Cognitivas": {"Q1": "O seu trabalho exige que você pense rápido?", "Q2": "Você precisa lembrar de muitas coisas no trabalho?", "Q3": "O seu trabalho exige que você tome decisões difíceis?"},
        "2. Exigências Emocionais": {"Q4": "O seu trabalho exige que você esconda suas emoções?", "Q5": "Você precisa lidar com pessoas difíceis no trabalho?"},
        "3. Ritmo de Trabalho": {"Q6": "Você tem que trabalhar muito intensamente?", "Q7": "O seu trabalho exige que você seja rápido?"}
    },
    "🛠️ Organização do Trabalho e Autonomia": {
        "4. Influência no Trabalho": {"Q8": "Você tem influência sobre como realiza seu trabalho?", "Q9": "Você pode decidir quando fazer suas tarefas?"},
        "5. Possibilidades de Desenvolvimento": {"Q10": "O seu trabalho oferece oportunidades para aprender coisas novas?", "Q11": "Você sente que pode se desenvolver profissionalmente?"},
        "6. Sentido do Trabalho": {"Q12": "Você sente que o seu trabalho é significativo?", "Q13": "Você sente orgulho do seu trabalho?"},
        "7. Previsibilidade": {"Q14": "Você sabe com antecedência o que vai fazer no trabalho?", "Q15": "Você recebe informações suficientes sobre mudanças no trabalho?"},
        "8. Clareza de Papéis": {"Q16": "Você sabe exatamente quais são suas responsabilidades?", "Q17": "Você entende o que se espera de você no trabalho?"}
    },
    "👥 Relações e Liderança": {
        "9. Reconhecimento": {"Q18": "Seu trabalho é reconhecido pelos seus superiores?", "Q19": "Você recebe elogios pelo seu desempenho?"},
        "10. Apoio Social dos Colegas": {"Q20": "Você recebe ajuda dos seus colegas quando precisa?", "Q21": "Você sente que pode contar com seus colegas?"},
        "11. Apoio Social da Liderança": {"Q22": "Seu supervisor se preocupa com você?", "Q23": "Você recebe apoio da liderança quando enfrenta dificuldades?"},
        "12. Qualidade da Liderança": {"Q24": "Seu supervisor é bom em resolver conflitos?", "Q25": "Seu supervisor comunica claramente as metas?"},
        "13. Justiça Organizacional": {"Q26": "As decisões no trabalho são tomadas de forma justa?", "Q27": "Você sente que é tratado com respeito?"},
        "14. Confiança Vertical": {"Q28": "Você confia na liderança da sua organização?", "Q29": "A liderança age com transparência?"}
    },
    "🏢 Ambiente e Segurança": {
        "15. Comunidade no Local de Trabalho": {"Q30": "Você sente que pertence ao seu grupo de trabalho?", "Q31": "Há um bom espírito de equipe?"},
        "16. Segurança no Trabalho": {"Q32": "Você sente que seu emprego está seguro?", "Q33": "Você teme ser demitido?"},
        "17. Comportamentos Ofensivos": {"Q34": "Você já foi alvo de bullying no trabalho?", "Q35": "Já presenciou comportamentos agressivos entre colegas?"}
    },
    "❤️ Saúde e Bem-Estar": {
        "18. Estresse": {"Q36": "Você se sente estressado com o trabalho?", "Q37": "O trabalho afeta negativamente sua saúde mental?"},
        "19. Sintomas Físicos": {"Q38": "Você tem dores físicas relacionadas ao trabalho?", "Q39": "O trabalho causa cansaço físico excessivo?"},
        "20. Problemas de Sono": {"Q40": "Você tem dificuldade para dormir por causa do trabalho?", "Q41": "Você acorda pensando em problemas do trabalho?"},
        "21. Satisfação no Trabalho": {"Q42": "Você está satisfeito com seu trabalho atual?", "Q43": "Você recomendaria seu trabalho para outras pessoas?"},
        "22. Engajamento no Trabalho": {"Q44": "Você se sente envolvido com as atividades do seu trabalho?", "Q45": "Você se sente motivado para ir trabalhar?"}
    }
}

total_perguntas = sum(len(perguntas) for dim in dimensoes_agrupadas.values() for perguntas in dim.values())

# --- INTERFACE PRINCIPAL ---
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
            for q_key, q_text in perguntas.items():
                # A lógica para exibir os radio buttons e guardar as respostas
                resposta_guardada = st.session_state.respostas_br.get(q_key)
                indice = opcoes_escala.index(resposta_guardada) if resposta_guardada in opcoes_escala else None
                
                resposta = st.radio(
                    label=q_text,
                    options=opcoes_escala,
                    key=q_key,
                    horizontal=True,
                    index=indice
                )
                if resposta:
                    st.session_state.respostas_br[q_key] = resposta
            st.markdown("---")

# --- LÓGICA DE FINALIZAÇÃO E ENVIO ---
if progresso == 1.0:
    st.success("🎉 **Excelente! Você respondeu a todas as perguntas.**")
    if st.button("Enviar Respostas", type="primary", use_container_width=True):
        with st.spinner('Calculando e enviando...'):
            
            # Combina as respostas com as pontuações calculadas
            resultados_dimensoes = motor.calcular_dimensoes(st.session_state.respostas_br)
            dados_completos = {**st.session_state.respostas_br, **resultados_dimensoes}
            
            # CORREÇÃO FINAL: Converte todos os valores para string antes de salvar.
            dados_formatados_para_salvar = {k: str(v) if v is not None else "" for k, v in dados_completos.items()}

            if salvar_dados(dados_formatados_para_salvar):
                # Limpa as respostas da sessão para permitir um novo preenchimento
                chaves_para_limpar = list(st.session_state.respostas_br.keys())
                for key in chaves_para_limpar:
                    del st.session_state.respostas_br[key]
                
                st.balloons()
                st.success("✅ Respostas enviadas com sucesso. Muito obrigado!")
                st.info("Pode fechar esta janela.")
                st.rerun() # Reinicia a página para o estado inicial
            # Se salvar_dados falhar, a mensagem de erro já é exibida pela função
else:
    st.warning("Por favor, navegue por todas as abas e responda às perguntas restantes.")

