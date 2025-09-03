import statistics

# Dicionário que converte a resposta em texto para uma pontuação de 0 a 100
pontuacao_map = {
    "Nunca": 0,
    "Raramente": 25,
    "Às vezes": 50,
    "Frequentemente": 75,
    "Sempre": 100,
    None: None
}

# Definição das 22 dimensões e quais perguntas pertencem a cada uma
definicao_dimensoes = {
    "1. Exigências Cognitivas": ["Q1", "Q2", "Q3"],
    "2. Exigências Emocionais": ["Q4", "Q5"],
    "3. Ritmo de Trabalho": ["Q6", "Q7"],
    "4. Influência no Trabalho": ["Q8", "Q9"],
    "5. Possibilidades de Desenvolvimento": ["Q10", "Q11"],
    "6. Sentido do Trabalho": ["Q12", "Q13"],
    "7. Previsibilidade": ["Q14", "Q15"],
    "8. Clareza de Papéis": ["Q16", "Q17"],
    "9. Reconhecimento": ["Q18", "Q19"],
    "10. Apoio Social dos Colegas": ["Q20", "Q21"],
    "11. Apoio Social da Liderança": ["Q22", "Q23"],
    "12. Qualidade da Liderança": ["Q24", "Q25"],
    "13. Justiça Organizacional": ["Q26", "Q27"],
    "14. Confiança Vertical": ["Q28", "Q29"],
    "15. Comunidade no Local de Trabalho": ["Q30", "Q31"],
    "16. Segurança no Trabalho": ["Q32", "Q33"],
    "17. Comportamentos Ofensivos": ["Q34", "Q35"],
    "18. Estresse": ["Q36", "Q37"],
    "19. Sintomas Físicos": ["Q38", "Q39"],
    "20. Problemas de Sono": ["Q40", "Q41"],
    "21. Satisfação no Trabalho": ["Q42", "Q43"],
    "22. Engajamento no Trabalho": ["Q44", "Q45"]
}
# OBS: O número de perguntas no esqueleto original era 45. Ajustei a numeração das chaves (Q1 a Q45) para corresponder.

def calcular_dimensoes(respostas_usuario):
    """
    Calcula a pontuação média para cada dimensão do COPSOQ.
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
