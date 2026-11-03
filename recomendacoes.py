"""Heurísticas explícitas: os modelos aprendem grupos, não a eficácia das missões."""

from dados import FEATURES

# Limiares de projeto, não verdades científicas nem parâmetros aprendidos.
REGRAS = [
    {'feature': 'cobertura_coleta_seletiva_pct', 'operador': '<', 'limiar': 30,
     'categoria': 'reducao_e_reutilizacao',
     'orientacao': 'Reduza descartáveis e reutilize materiais limpos e seguros.'},
    {'feature': 'recuperacao_reciclaveis_pct', 'operador': '<', 'limiar': 5,
     'categoria': 'separacao_e_educacao',
     'orientacao': 'Aprenda a separar recicláveis e compartilhe orientações locais verificadas.'},
    {'feature': 'pontos_entrega_voluntaria_por_mil_hab', 'operador': '>', 'limiar': 0,
     'categoria': 'entrega_voluntaria',
     'orientacao': 'Consulte endereço, materiais aceitos e funcionamento de ponto de entrega oficial.'},
    {'feature': 'massa_residuos_urbanos_kg_hab_dia', 'operador': '>', 'limiar': 1,
     'categoria': 'consumo_consciente',
     'orientacao': 'Planeje compras e evite descartáveis desnecessários.'},
    {'feature': 'disposicao_final_inadequada_pct', 'operador': '>', 'limiar': 50,
     'categoria': 'descarte_responsavel',
     'orientacao': 'Busque informações oficiais de coleta e descarte; não entre em áreas de disposição.'},
]


def associar_missoes(perfis):
    for perfil in perfis.values():
        recomendacoes = []
        for regra in REGRAS:
            valor = perfil['medias'][regra['feature']]
            atende = valor < regra['limiar'] if regra['operador'] == '<' else valor > regra['limiar']
            if atende:
                recomendacoes.append({
                    'categoria': regra['categoria'], 'orientacao': regra['orientacao'],
                    'motivo_grupo': f"Média de {regra['feature']}: {valor:.2f}; regra {regra['operador']} {regra['limiar']}.",
                })
        if not recomendacoes:
            recomendacoes.append({
                'categoria': 'consumo_consciente',
                'orientacao': 'Planeje compras e evite descartáveis desnecessários.',
                'motivo_grupo': 'Sugestão geral quando nenhum limiar específico é atendido.',
            })
        perfil['recomendacoes'] = recomendacoes
    return perfis


def descrever_grupos(pipeline, dados):
    grupos = dados[FEATURES].copy()
    grupos['grupo'] = pipeline.predict(dados[FEATURES])
    medias = grupos.groupby('grupo')[FEATURES].mean()
    tamanhos = grupos.groupby('grupo').size()
    return {
        str(grupo): {
            'nome': f'Grupo {grupo}: coleta seletiva média {linha.cobertura_coleta_seletiva_pct:.1f}%',
            'municipios': int(tamanhos.loc[grupo]),
            'medias': {nome: float(linha[nome]) for nome in FEATURES},
        }
        for grupo, linha in medias.iterrows()
    }
