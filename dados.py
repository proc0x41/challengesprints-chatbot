"""Leitura da base original, sem criar rótulos artificiais."""

from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent if '__file__' in globals() else Path.cwd()
ARQUIVO_DADOS = BASE / 'alpha4_sinisa_ibge_municipios.csv'
SEMENTE = 42

# Identificadores, binários derivados e o gap redundante ficam fora das distâncias.
FEATURES = [
    'taxa_urbanizacao_pct',
    'densidade_populacional_hab_km2',
    'cobertura_coleta_residuos_pct',
    'cobertura_coleta_seletiva_pct',
    'pontos_entrega_voluntaria_por_mil_hab',
    'massa_residuos_urbanos_kg_hab_dia',
    'disposicao_final_inadequada_pct',
    'recuperacao_reciclaveis_pct',
]
LOG_FEATURES = [
    'densidade_populacional_hab_km2',
    'pontos_entrega_voluntaria_por_mil_hab',
    'massa_residuos_urbanos_kg_hab_dia',
]
PERCENTUAIS = [nome for nome in FEATURES if nome.endswith('_pct')]


def carregar_dados(caminho=ARQUIVO_DADOS):
    dados = pd.read_csv(caminho, dtype={'codigo_ibge': str})
    obrigatorias = ['codigo_ibge', 'municipio', 'uf', 'regiao', *FEATURES]
    if not set(obrigatorias).issubset(dados.columns):
        raise ValueError('A base não contém as colunas necessárias.')
    if dados[obrigatorias].isna().any().any():
        raise ValueError('Há campos obrigatórios ausentes na base.')
    if dados.codigo_ibge.duplicated().any():
        raise ValueError('Há códigos IBGE duplicados.')
    if not dados.codigo_ibge.str.fullmatch(r'[0-9]{7}').all():
        raise ValueError('Código IBGE deve ter sete dígitos.')
    valores = dados[FEATURES].to_numpy(dtype=float)
    if not np.isfinite(valores).all() or (valores < 0).any():
        raise ValueError('Indicadores devem ser números finitos não negativos.')
    if (dados[PERCENTUAIS] > 100).any().any():
        raise ValueError('Percentuais devem estar entre zero e cem.')
    if (dados.cobertura_coleta_seletiva_pct > dados.cobertura_coleta_residuos_pct).any():
        raise ValueError('Coleta seletiva não pode superar a cobertura total.')
    return dados
