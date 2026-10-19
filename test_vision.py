import unittest
from pathlib import Path

import cv2
import numpy as np

from vision import DEFAULT_KIT, compare, detect, sample


class VisionTests(unittest.TestCase):
    def check(self, kind):
        return compare(DEFAULT_KIT, detect(sample(kind))[2])

    def test_complete(self):
        self.assertTrue(self.check('correto')[0])

    def test_missing(self):
        ok, rows = self.check('faltando')
        self.assertFalse(ok)
        self.assertEqual(next(r['Diferença'] for r in rows if r['Classe'] == 'Verde / Círculo'), -1)

    def test_extra(self):
        self.assertFalse(self.check('extra')[0])

    def test_empty(self):
        objects = detect(np.full((400, 400, 3), 240, np.uint8))[2]
        self.assertEqual(objects, [])
        self.assertFalse(compare(DEFAULT_KIT, objects)[0])

    def test_unexpected_class(self):
        self.assertFalse(compare(DEFAULT_KIT, [{'classe': 'Azul / Círculo'}])[0])

    def test_invalid(self):
        with self.assertRaises(ValueError):
            detect(None)

    def test_noise(self):
        im = sample()
        rng = np.random.default_rng(42)
        im = np.clip(im.astype(float) + rng.normal(0, 6, im.shape), 0, 255).astype(np.uint8)
        self.assertTrue(compare(DEFAULT_KIT, detect(im)[2])[0])


class ReferenceImageTests(unittest.TestCase):
    """Regressão sobre os arquivos de exemplos/, e não sobre imagens geradas
    em memória. Isso cobre também a leitura do PNG pelo OpenCV, que é o
    caminho real de uma conferência por imagem. Se o limiar de confiança, a
    faixa de cor ou a área mínima mudarem, estes casos acusam."""

    CAMINHO = Path(__file__).resolve().parent / 'exemplos'

    def carregar(self, nome):
        caminho = self.CAMINHO / f'{nome}.png'
        self.assertTrue(caminho.exists(), f'imagem de referência ausente: {caminho}')
        imagem = cv2.imread(str(caminho))
        self.assertIsNotNone(imagem, f'OpenCV não conseguiu ler {caminho}')
        return imagem

    def conferir(self, nome):
        return compare(DEFAULT_KIT, detect(self.carregar(nome))[2])

    def diferenca(self, linhas, classe):
        return next(r['Diferença'] for r in linhas if r['Classe'] == classe)

    def test_correto_aprova(self):
        aprovado, linhas = self.conferir('correto')
        self.assertTrue(aprovado)
        for linha in linhas:
            self.assertEqual(linha['Diferença'], 0, linha['Classe'])

    def test_faltando_acusa_o_circulo_ausente(self):
        aprovado, linhas = self.conferir('faltando')
        self.assertFalse(aprovado)
        self.assertEqual(self.diferenca(linhas, 'Verde / Círculo'), -1)
        self.assertEqual(self.diferenca(linhas, 'Azul / Retângulo'), 0)
        self.assertEqual(self.diferenca(linhas, 'Amarelo / Triângulo'), 0)

    def test_extra_acusa_o_circulo_a_mais(self):
        aprovado, linhas = self.conferir('extra')
        self.assertFalse(aprovado)
        self.assertEqual(self.diferenca(linhas, 'Verde / Círculo'), 1)

    def test_detecta_exatamente_tres_objetos_na_imagem_correta(self):
        objetos = detect(self.carregar('correto'))[2]
        self.assertEqual(len(objetos), 3)
        self.assertEqual(
            sorted(o['classe'] for o in objetos),
            ['Amarelo / Triângulo', 'Azul / Retângulo', 'Verde / Círculo'],
        )

    def test_imagem_anotada_tem_o_mesmo_formato_da_entrada(self):
        imagem = self.carregar('correto')
        anotada, mascara, _ = detect(imagem)
        self.assertEqual(anotada.shape, imagem.shape)
        self.assertEqual(mascara.shape, imagem.shape[:2])


if __name__ == '__main__':
    unittest.main()
