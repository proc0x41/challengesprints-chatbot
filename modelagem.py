"""Pipelines e comparação de agrupamentos sem usar identificadores nas distâncias."""

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.mixture import GaussianMixture
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
