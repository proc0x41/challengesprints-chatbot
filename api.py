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
        if artefato.get('formato') != 1:
            raise ValueError('Formato de modelo incompatível.')
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
