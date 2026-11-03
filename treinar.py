"""Treinamento offline; a API apenas carrega o artefato gerado aqui."""

import hashlib
import json
from importlib.metadata import version

import joblib

from dados import ARQUIVO_DADOS, BASE, FEATURES, PERCENTUAIS, SEMENTE, carregar_dados
from modelagem import comparar_modelos, avaliar_finalistas, criar_kmeans, criar_mistura, separar_dados
from recomendacoes import REGRAS, associar_missoes, descrever_grupos


def executar_treinamento():
    dados = carregar_dados()
    treino, validacao, teste = separar_dados(dados)
    tabela, candidatos = comparar_modelos(treino, validacao)
    nome, k, avaliacao = avaliar_finalistas(tabela, candidatos, teste)
    # Somente depois da avaliação, reajuste em toda a base para disponibilização.
    construir = criar_kmeans if nome == 'kmeans' else criar_mistura
    final = construir(k).fit(dados[FEATURES])
    perfis = associar_missoes(descrever_grupos(final, dados))
    metricas = {
        'semente': SEMENTE,
        'particao': {'treino': len(treino), 'validacao': len(validacao), 'teste': len(teste)},
        'vencedor': {'modelo': nome, 'k': k},
        'candidatos_validacao': tabela.to_dict(orient='records'),
        'finalistas_teste': avaliacao,
        'observacao': 'Métricas de teste são dos pipelines ajustados apenas no treino; o artefato final foi reajustado em toda a base.',
    }
    artefato = {
        'formato': 1, 'pipeline': final, 'modelo': nome, 'k': k,
        'features': FEATURES, 'percentuais': PERCENTUAIS, 'perfis': perfis, 'regras': REGRAS,
        'catalogo': dados[['codigo_ibge', 'municipio', 'uf', *FEATURES]].set_index('codigo_ibge').to_dict(orient='index'),
        'limites_observados': {nome: float(dados[nome].max()) for nome in FEATURES},
        'ano_referencia': 2023, 'metricas': metricas,
        'sha256_base': hashlib.sha256(ARQUIVO_DADOS.read_bytes()).hexdigest(),
        'versoes': {nome: version(nome) for nome in ['numpy', 'pandas', 'scikit-learn', 'Flask', 'joblib']},
    }
    joblib.dump(artefato, BASE / 'modelo_alpha4.joblib', compress=3)
    (BASE / 'metricas.json').write_text(json.dumps(metricas, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    (BASE / 'perfis_grupos.json').write_text(json.dumps(perfis, ensure_ascii=False, indent=2), encoding='utf-8')
    return dados, tabela, artefato


if __name__ == '__main__':
    _, tabela, artefato = executar_treinamento()
    print(tabela.to_string(index=False))
    print(json.dumps(artefato['metricas']['finalistas_teste'], indent=2))
    print('Selecionado:', artefato['modelo'], 'com', artefato['k'], 'grupos.')
