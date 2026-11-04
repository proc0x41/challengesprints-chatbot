"""API independente: apenas este arquivo e modelo_alpha4.joblib são necessários."""

import math
import os
from pathlib import Path

import joblib
import pandas as pd
from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException


def validar_indicadores(indicadores, artefato):
    if not isinstance(indicadores, dict) or set(indicadores) != set(artefato['features']):
        raise ValueError('indicadores deve conter exatamente as oito features informadas em /modelo.')
    for nome, valor in indicadores.items():
        try:
            finito = isinstance(valor, (int, float)) and not isinstance(valor, bool) and math.isfinite(valor)
        except OverflowError:
            finito = False
        if not finito or valor < 0:
            raise ValueError(f'{nome} deve ser um número finito não negativo.')
        if nome in artefato['percentuais'] and valor > 100:
            raise ValueError(f'{nome} deve estar entre zero e cem.')
    if indicadores['cobertura_coleta_seletiva_pct'] > indicadores['cobertura_coleta_residuos_pct']:
        raise ValueError('A cobertura seletiva não pode superar a cobertura total.')


def validar_artefato(artefato):
    obrigatorias = {
        'formato', 'pipeline', 'modelo', 'k', 'features', 'percentuais', 'perfis',
        'regras', 'ano_referencia', 'metricas', 'versoes', 'catalogo', 'limites_observados',
    }
    if not isinstance(artefato, dict) or not obrigatorias.issubset(artefato):
        raise ValueError('Artefato incompleto: faltam campos exigidos pela API.')
    if artefato['formato'] != 1 or not callable(getattr(artefato['pipeline'], 'predict', None)):
        raise ValueError('Formato ou pipeline de previsão incompatível.')
    if artefato['modelo'] not in ('kmeans', 'mistura_gaussiana') or type(artefato['k']) is not int or artefato['k'] < 2:
        raise ValueError('Metadados do modelo inválidos.')
    esperadas = {
        'taxa_urbanizacao_pct', 'densidade_populacional_hab_km2',
        'cobertura_coleta_residuos_pct', 'cobertura_coleta_seletiva_pct',
        'pontos_entrega_voluntaria_por_mil_hab', 'massa_residuos_urbanos_kg_hab_dia',
        'disposicao_final_inadequada_pct', 'recuperacao_reciclaveis_pct',
    }
    features = artefato['features']
    if not isinstance(features, list) or len(features) != 8 or set(features) != esperadas:
        raise ValueError('Features do artefato incompatíveis com a API.')
    if set(artefato['percentuais']) != {nome for nome in features if nome.endswith('_pct')}:
        raise ValueError('Metadados dos percentuais inválidos.')
    if not isinstance(artefato['regras'], list) or type(artefato['ano_referencia']) is not int:
        raise ValueError('Regras ou ano de referência inválidos.')
    for nome in ['perfis', 'metricas', 'versoes', 'catalogo']:
        if not isinstance(artefato[nome], dict) or not artefato[nome]:
            raise ValueError(f'{nome} deve ser um objeto não vazio.')
    for grupo in range(artefato['k']):
        perfil = artefato['perfis'].get(str(grupo))
        if not isinstance(perfil, dict) or not isinstance(perfil.get('nome'), str) or not isinstance(perfil.get('recomendacoes'), list):
            raise ValueError('Perfil de grupo incompleto.')
        for recomendacao in perfil['recomendacoes']:
            if not isinstance(recomendacao, dict) or not all(
                isinstance(recomendacao.get(campo), str) for campo in ['categoria', 'orientacao', 'motivo_grupo']
            ):
                raise ValueError('Recomendação de grupo incompleta.')
    validar_indicadores(artefato['limites_observados'], artefato)
    for registro in artefato['catalogo'].values():
        if not isinstance(registro, dict) or not all(isinstance(registro.get(campo), str) for campo in ['municipio', 'uf']):
            raise ValueError('Registro do catálogo municipal incompleto.')
        validar_indicadores({nome: registro[nome] for nome in features}, artefato)


def criar_app(caminho_modelo=None):
    app = Flask(__name__)
    app.json.ensure_ascii = False
    app.config['MAX_CONTENT_LENGTH'] = 32 * 1024

    @app.errorhandler(HTTPException)
    def tratar_http(erro):
        return jsonify({'erro': erro.description}), erro.code

    pasta = Path(__file__).resolve().parent if '__file__' in globals() else Path.cwd()
    caminho = Path(caminho_modelo or os.getenv('ALPHA4_MODELO', pasta / 'modelo_alpha4.joblib'))
    # Carrega uma única vez na inicialização. Nunca há fit dentro das rotas.
    try:
        artefato = joblib.load(caminho)
        validar_artefato(artefato)
    except Exception:
        app.logger.exception('Não foi possível carregar o modelo local.')
        artefato = None

    @app.get('/saude')
    def saude():
        return jsonify({'status': 'ok' if artefato else 'indisponivel'}), 200 if artefato else 503

    @app.get('/modelo')
    def modelo():
        if artefato is None:
            return jsonify({'erro': 'Modelo indisponível.'}), 503
        return jsonify({chave: artefato[chave] for chave in [
            'modelo', 'k', 'features', 'perfis', 'regras', 'ano_referencia', 'metricas', 'versoes',
        ]})

    def prever(indicadores, municipio=None):
        entrada = pd.DataFrame([indicadores], columns=artefato['features'])
        grupo = int(artefato['pipeline'].predict(entrada)[0])
        perfil = artefato['perfis'][str(grupo)]
        recomendacoes = [item for item in perfil['recomendacoes'] if
            item['categoria'] != 'entrega_voluntaria'
            or indicadores['pontos_entrega_voluntaria_por_mil_hab'] > 0]
        if not recomendacoes:
            recomendacoes = [{
                'categoria': 'consumo_consciente',
                'orientacao': 'Planeje compras e evite descartáveis desnecessários.',
                'motivo_grupo': 'Sugestão geral após excluir entrega voluntária sem indicador local positivo.',
            }]
        return jsonify({
            'modelo': artefato['modelo'], 'grupo': grupo, 'perfil': perfil['nome'],
            'municipio': municipio, 'ano_referencia': artefato['ano_referencia'],
            'recomendacoes': recomendacoes,
            'fora_da_faixa_observada': [nome for nome in artefato['features']
                if indicadores[nome] > artefato['limites_observados'][nome]],
            'aviso': 'Sugestões por contexto municipal de 2023, baseadas em regras de projeto; não preveem engajamento individual. Confirme serviços locais e não manipule resíduos perigosos.',
        })

    @app.get('/municipios/<codigo>')
    def consultar_municipio(codigo):
        if artefato is None:
            return jsonify({'erro': 'Modelo indisponível.'}), 503
        registro = artefato['catalogo'].get(codigo)
        if registro is None:
            return jsonify({'erro': 'Município não encontrado na base de 2023.'}), 404
        indicadores = {nome: registro[nome] for nome in artefato['features']}
        return prever(indicadores, {'codigo_ibge': codigo, 'nome': registro['municipio'], 'uf': registro['uf']})

    @app.post('/prever')
    def receber_previsao():
        if artefato is None:
            return jsonify({'erro': 'Modelo indisponível.'}), 503
        corpo = request.get_json()
        if isinstance(corpo, dict) and set(corpo) == {'codigo_ibge'}:
            codigo = corpo['codigo_ibge']
            if not isinstance(codigo, str) or len(codigo) != 7 or not codigo.isascii() or not codigo.isdigit():
                return jsonify({'erro': 'codigo_ibge deve ser um texto com sete dígitos.'}), 422
            return consultar_municipio(codigo)
        if not isinstance(corpo, dict) or set(corpo) != {'indicadores'}:
            return jsonify({'erro': 'Envie apenas codigo_ibge ou indicadores.'}), 422
        try:
            validar_indicadores(corpo['indicadores'], artefato)
        except ValueError as erro:
            return jsonify({'erro': str(erro)}), 422
        return prever(corpo['indicadores'])

    return app


app = criar_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=int(os.getenv('PORT', '5000')), debug=False)
