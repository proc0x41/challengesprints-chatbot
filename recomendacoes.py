"""Heurísticas explícitas: os modelos aprendem grupos, não a eficácia das missões."""

from dados import FEATURES


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
