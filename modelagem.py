"""Pipelines e comparação de agrupamentos sem usar identificadores nas distâncias."""

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.mixture import GaussianMixture
from sklearn.metrics import calinski_harabasz_score, davies_bouldin_score, silhouette_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler

from dados import FEATURES, LOG_FEATURES, PERCENTUAIS, SEMENTE


def separar_dados(dados):
    treino, restante = train_test_split(
        dados, test_size=0.4, random_state=SEMENTE, stratify=dados.regiao,
    )
    validacao, teste = train_test_split(
        restante, test_size=0.5, random_state=SEMENTE, stratify=restante.regiao,
    )
    return treino.copy(), validacao.copy(), teste.copy()


def criar_preparo():
    # log1p comprime caudas longas sem remover observações nem alterar percentuais.
    transformar = ColumnTransformer([
        ('log', FunctionTransformer(np.log1p, feature_names_out='one-to-one'), LOG_FEATURES),
        ('percentuais', 'passthrough', PERCENTUAIS),
    ], remainder='drop')
    return Pipeline([('transformar', transformar), ('escalonar', StandardScaler())])


def criar_kmeans(k):
    return Pipeline([
        ('preparo', criar_preparo()),
        ('modelo', KMeans(n_clusters=k, n_init=20, random_state=SEMENTE)),
    ])


def criar_mistura(k):
    return Pipeline([
        ('preparo', criar_preparo()),
        ('modelo', GaussianMixture(
            n_components=k, covariance_type='full', n_init=5,
            max_iter=500, reg_covar=1e-5, random_state=SEMENTE,
        )),
    ])


def medir_grupos(pipeline, dados, k):
    valores = pipeline.named_steps['preparo'].transform(dados[FEATURES])
    grupos = pipeline.predict(dados[FEATURES])
    contagens = np.bincount(grupos, minlength=k)
    resultado = {
        'tamanhos': contagens.tolist(),
        'menor_proporcao': float(contagens.min() / len(dados)),
        'silhouette': None, 'davies_bouldin': None, 'calinski_harabasz': None,
    }
    if 1 < len(np.unique(grupos)) < len(grupos):
        resultado.update({
            'silhouette': float(silhouette_score(valores, grupos)),
            'davies_bouldin': float(davies_bouldin_score(valores, grupos)),
            'calinski_harabasz': float(calinski_harabasz_score(valores, grupos)),
        })
    return resultado


def comparar_modelos(treino, validacao):
    linhas, candidatos = [], {}
    for nome, construir in [('kmeans', criar_kmeans), ('mistura_gaussiana', criar_mistura)]:
        for k in range(2, 7):
            pipeline = construir(k).fit(treino[FEATURES])
            metricas = medir_grupos(pipeline, validacao, k)
            convergiu = bool(getattr(pipeline.named_steps['modelo'], 'converged_', True))
            linhas.append({
                'modelo': nome, 'k': k, 'convergiu': convergiu,
                **{campo: valor for campo, valor in metricas.items() if campo != 'tamanhos'},
                'elegivel': convergiu and metricas['menor_proporcao'] >= 0.02,
            })
            candidatos[(nome, k)] = pipeline
    tabela = pd.DataFrame(linhas).sort_values('silhouette', ascending=False)
    if not tabela.elegivel.any():
        raise ValueError('Nenhum candidato convergiu com ao menos 2% em cada grupo de validação.')
    return tabela, candidatos


def avaliar_finalistas(tabela, candidatos, teste):
    # A seleção usa somente validação; teste é observado após fixar os finalistas.
    finalistas = tabela[tabela.elegivel].groupby('modelo', sort=False).head(1)
    resultados = {}
    for linha in finalistas.itertuples():
        resultados[linha.modelo] = {
            'k': int(linha.k),
            **medir_grupos(candidatos[(linha.modelo, linha.k)], teste, linha.k),
        }
    vencedor = tabela[tabela.elegivel].iloc[0]
    return str(vencedor.modelo), int(vencedor.k), resultados
