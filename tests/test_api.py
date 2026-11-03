import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import joblib

from api import criar_app
from dados import BASE


class TestAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = criar_app()
        cls.app.testing = True
        cls.cliente = cls.app.test_client()
        cls.artefato = joblib.load(BASE / 'modelo_alpha4.joblib')
        registro = cls.artefato['catalogo']['1100015']
        cls.indicadores = {nome: registro[nome] for nome in cls.artefato['features']}

    def test_saude_e_metadados(self):
        self.assertEqual(self.cliente.get('/saude').status_code, 200)
        self.assertEqual(self.cliente.get('/modelo').json['modelo'], self.artefato['modelo'])

    def test_codigo_get_e_post_consistentes_sem_novo_treino(self):
        with patch('sklearn.pipeline.Pipeline.fit', side_effect=AssertionError('Não treinar na API')):
            get = self.cliente.get('/municipios/1100015')
            post = self.cliente.post('/prever', json={'codigo_ibge': '1100015'})
        self.assertEqual(get.status_code, 200)
        self.assertEqual(get.json, post.json)
        self.assertEqual(get.json['municipio']['nome'], "Alta Floresta D'Oeste")

    def test_indicadores_validos_e_prevencao_de_pev_inexistente(self):
        indicadores = {**self.indicadores, 'pontos_entrega_voluntaria_por_mil_hab': 0}
        resposta = self.cliente.post('/prever', json={'indicadores': indicadores})
        self.assertEqual(resposta.status_code, 200)
        self.assertNotIn('entrega_voluntaria', [r['categoria'] for r in resposta.json['recomendacoes']])

    def test_entradas_invalidas(self):
        casos = [None, [], {}, {'codigo_ibge': 1100015}, {'codigo_ibge': 'abc'},
                 {'codigo_ibge': '1100015', 'indicadores': self.indicadores}, {'indicadores': {}}]
        for corpo in casos:
            with self.subTest(corpo=corpo):
                resposta = self.cliente.post('/prever', data=__import__('json').dumps(corpo), content_type='application/json')
                self.assertEqual(resposta.status_code, 422)
        for valor in [-1, 101, True, '50', float('nan'), float('inf')]:
            indicadores = {**self.indicadores, 'taxa_urbanizacao_pct': valor}
            self.assertEqual(self.cliente.post('/prever', json={'indicadores': indicadores}).status_code, 422)
        indicadores = {**self.indicadores, 'cobertura_coleta_seletiva_pct': 100}
        self.assertEqual(self.cliente.post('/prever', json={'indicadores': indicadores}).status_code, 422)

    def test_formato_http_e_municipio_ausente(self):
        self.assertEqual(self.cliente.post('/prever', data='{', content_type='application/json').status_code, 400)
        self.assertEqual(self.cliente.post('/prever', data='texto').status_code, 415)
        self.assertEqual(self.cliente.get('/municipios/0000000').status_code, 404)
        self.assertEqual(self.cliente.get('/rota-inexistente').status_code, 404)
        self.assertEqual(self.cliente.post('/prever', data='x' * 33000, content_type='application/json').status_code, 413)

    def test_modelo_ausente_retorna_503(self):
        with tempfile.TemporaryDirectory() as pasta:
            with self.assertLogs(level='ERROR'):
                cliente = criar_app(Path(pasta) / 'ausente.joblib').test_client()
            self.assertEqual(cliente.get('/saude').status_code, 503)
            self.assertEqual(cliente.post('/prever', json={'codigo_ibge': '1100015'}).status_code, 503)
