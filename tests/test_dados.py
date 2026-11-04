import unittest

from dados import FEATURES, carregar_dados
from modelagem import criar_preparo, separar_dados


class TestDados(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dados = carregar_dados()

    def test_base_fornecida_e_identificadores(self):
        self.assertEqual(self.dados.shape, (4775, 31))
        self.assertEqual(self.dados.uf.nunique(), 27)
        self.assertEqual(self.dados.ano_referencia_sinisa.unique().tolist(), [2023])
        self.assertFalse(self.dados.codigo_ibge.duplicated().any())

    def test_particoes_disjuntas_e_completas(self):
        treino, validacao, teste = separar_dados(self.dados)
        indices = [set(parte.index) for parte in [treino, validacao, teste]]
        self.assertEqual([len(parte) for parte in indices], [2865, 955, 955])
        self.assertFalse(indices[0] & indices[1] or indices[0] & indices[2] or indices[1] & indices[2])
        self.assertEqual(set.union(*indices), set(self.dados.index))

    def test_preparo_so_aprende_do_treino(self):
        treino, validacao, _ = separar_dados(self.dados)
        preparo = criar_preparo().fit(treino[FEATURES])
        self.assertEqual(preparo.named_steps['escalonar'].n_samples_seen_, len(treino))
        self.assertEqual(preparo.transform(validacao[FEATURES]).shape, (955, 8))
        self.assertNotIn('codigo_ibge', FEATURES)
        self.assertNotIn('possui_coleta_seletiva', FEATURES)
        self.assertNotIn('gap_coleta_seletiva_pct', FEATURES)
