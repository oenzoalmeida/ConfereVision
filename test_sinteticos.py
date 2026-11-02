"""Cobertura do conjunto sintético de robustez (exemplos/sinteticos)."""

import hashlib
import json
import shutil
import unittest
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parent
ROTULOS = ROOT / 'exemplos' / 'sinteticos' / 'rotulos-sinteticos.json'


class SyntheticSetTests(unittest.TestCase):
    def test_geracao_deterministica(self):
        """Regenerar as variações produz exatamente os mesmos bytes."""
        from exemplos.gerar_sinteticos import gerar

        destino = ROOT / 'exemplos' / 'sinteticos-tmp-teste'
        try:
            gerado = gerar(destino)
            esperado = {
                img['variacao']: img['sha256']
                for img in json.loads(ROTULOS.read_text(encoding='utf-8'))['images']
            }
            obtido = {img['variacao']: img['sha256'] for img in gerado['images']}
            self.assertEqual(obtido, esperado)
        finally:
            shutil.rmtree(destino, ignore_errors=True)

    def test_rotulos_integros(self):
        """Checksums batem, caixas cabem na imagem e classes são coerentes."""
        rotulos = json.loads(ROTULOS.read_text(encoding='utf-8'))
        self.assertGreaterEqual(len(rotulos['images']), 8)
        for entrada in rotulos['images']:
            arquivo = ROOT / entrada['file']
            self.assertEqual(hashlib.sha256(arquivo.read_bytes()).hexdigest(), entrada['sha256'])
            imagem = cv2.imread(str(arquivo))
            altura, largura = imagem.shape[:2]
            classes = set()
            for objeto in entrada['objects']:
                x, y, w, h = objeto['caixa']
                classes.add(objeto['classe'])
                self.assertGreaterEqual(x, 0)
                self.assertGreaterEqual(y, 0)
                self.assertLessEqual(x + w, largura)
                self.assertLessEqual(y + h, altura)
            self.assertEqual(classes, set(entrada['evaluated_classes']))

    def test_avaliacao_sintetica_consistente(self):
        """A avaliação roda e os totais fecham por classe (requer o modelo ONNX)."""
        if not (ROOT / 'models' / 'yolox.onnx').is_file():
            raise RuntimeError('Run python download_model.py before the ONNX integration suite.')
        from evaluate_photos import evaluate

        resultado = evaluate(ROTULOS)
        total_objetos = sum(
            len(img['objects']) for img in json.loads(ROTULOS.read_text(encoding='utf-8'))['images']
        )
        self.assertEqual(resultado['true_positives'] + resultado['false_negatives'], total_objetos)
        for classe, metricas in resultado['per_class'].items():
            self.assertEqual(
                metricas['true_positives'] + metricas['false_negatives'],
                total_por_classe(classe),
            )
        self.assertIn('Colher', resultado['per_class'])

    def test_sem_promessa_de_acuracia(self):
        """Os rótulos declaram explicitamente que não estimam acurácia real."""
        descricao = json.loads(ROTULOS.read_text(encoding='utf-8'))['description']
        self.assertIn('não estimam acurácia', descricao)


def total_por_classe(classe):
    rotulos = json.loads(ROTULOS.read_text(encoding='utf-8'))
    return sum(1 for img in rotulos['images'] for obj in img['objects'] if obj['classe'] == classe)


if __name__ == '__main__':
    unittest.main()
