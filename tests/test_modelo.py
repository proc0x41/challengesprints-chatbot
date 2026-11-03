import unittest

import joblib
import numpy as np

from dados import BASE, FEATURES, carregar_dados
from recomendacoes import associar_missoes


class TestModelo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artefato = joblib.load(BASE / 'modelo_alpha4.joblib')
        cls.dados = carregar_dados()

    def test_artefato_reabre_e_preve_todos_municipios(self):
        grupos = self.artefato['pipeline'].predict(self.dados[FEATURES])
        self.assertEqual(len(grupos), 4775)
        self.assertEqual(len(np.unique(grupos)), self.artefato['k'])
        self.assertEqual(sum(p['municipios'] for p in self.artefato['perfis'].values()), 4775)
        self.assertEqual(len(self.artefato['catalogo']), 4775)

    def test_avaliacao_contem_as_duas_familias_sem_usar_teste_na_selecao(self):
        metricas = self.artefato['metricas']
        self.assertEqual(set(metricas['finalistas_teste']), {'kmeans', 'mistura_gaussiana'})
        elegiveis = [linha for linha in metricas['candidatos_validacao'] if linha['elegivel']]
        melhor = max(elegiveis, key=lambda linha: linha['silhouette'])
        self.assertEqual(metricas['vencedor'], {'modelo': melhor['modelo'], 'k': melhor['k']})
        self.assertEqual(metricas['particao'], {'treino': 2865, 'validacao': 955, 'teste': 955})

    def test_regras_sao_separadas_do_modelo_e_dos_rotulos(self):
        perfil = {'0': {'medias': {nome: 0.0 for nome in FEATURES}}}
        categorias = [r['categoria'] for r in associar_missoes(perfil)['0']['recomendacoes']]
        self.assertIn('reducao_e_reutilizacao', categorias)
        self.assertNotIn('entrega_voluntaria', categorias)
        self.assertNotIn('categoria', FEATURES)
