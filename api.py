"""API independente: apenas este arquivo e modelo_alpha4.joblib são necessários."""

import math
import os
from pathlib import Path

import joblib
import pandas as pd
from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException


def criar_app(caminho_modelo=None):
    app = Flask(__name__)
    app.json.ensure_ascii = False
    app.config['MAX_CONTENT_LENGTH'] = 32 * 1024
    caminho = Path(caminho_modelo or os.getenv(
        'ALPHA4_MODELO', Path(__file__).resolve().with_name('modelo_alpha4.joblib'),
    ))
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

    return app
