import statistics

# Dicionário que converte a resposta em texto para uma pontuação de 0 a 100
pontuacao_map = {
    "Nunca": 0,
    "Raramente": 25,
    "Às vezes": 50,
    "Frequentemente": 75,
    "Sempre": 100,
    # Adicionar outras escalas se necessário, ex: para a pergunta de Saúde Geral
    "Muito ruim": 0, "Ruim": 25, "Razoável": 50, "Boa": 75, "Muito boa": 100,
    None: None
}

# Definição das dimensões e quais perguntas pertencem a cada uma,
# conforme a versão curta validada para o Brasil.
definicao_dimensoes = {
    "Ritmo de Trabalho": ["Q1", "Q2"],
    "Exigências Cognitivas": ["Q3", "Q4"],
    "Exigências Emocionais": ["Q5", "Q6"],
    "Influência": ["Q7", "Q8"],
    "Possibilidades de Desenvolvimento": ["Q9", "Q10"],
    "Sentido do Trabalho": ["Q11", "Q12"],
    "Comprometimento com o Local de Trabalho": ["Q13", "Q14"],
    "Previsibilidade": ["Q15", "Q16"],
    "Clareza de Papel": ["Q17"],
    "Conflito de Papel": ["Q18"],
    "Qualidade da Liderança": ["Q19", "Q20"],
    "Apoio Social do Superior": ["Q21"],
    "Apoio Social dos Colegas": ["Q22"],
    "Sentido de Comunidade": ["Q23"],
    "Insegurança no Emprego": ["Q24"],
    "Conflito Trabalho-Família": ["Q25"],
    "Satisfação no Trabalho": ["Q26"],
    "Saúde em Geral": ["Q27"],
    "Burnout": ["Q28"],
    "Estresse": ["Q29"],
    "Problemas de Sono": ["Q30"],
    "Sintomas Depressivos": ["Q31"],
    "Assédio Moral": ["Q32"],
}

def calcular_dimensoes(respostas_usuario):
    """
    Calcula a pontuação média para cada dimensão do COPSOQ II (Versão Curta BR).
    'respostas_usuario' é um dicionário com chaves 'Q1', 'Q2', etc.
    """
    resultados_finais = {}
    
    # Converte as respostas em texto para pontuações numéricas
    pontuacoes = {chave: pontuacao_map.get(resposta) for chave, resposta in respostas_usuario.items()}

    for nome_dimensao, chaves_perguntas in definicao_dimensoes.items():
        pontuacoes_da_dimensao = [pontuacoes[chave] for chave in chaves_perguntas if chave in pontuacoes and pontuacoes[chave] is not None]
        
        if pontuacoes_da_dimensao:
            media = statistics.mean(pontuacoes_da_dimensao)
            resultados_finais[nome_dimensao] = round(media, 2)
        else:
            resultados_finais[nome_dimensao] = None
            
    return resultados_finais

